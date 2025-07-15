import asyncio
import json

from loguru import logger
from sqlalchemy.exc import IntegrityError
import aio_pika

from app.config import QUEUE_NAME, RABBITMQ_URL

from app.database.database import InitDB
from app.database.crud import CRUDUsers, CRUDTransactions

from app.schemas.user import UserCreate
from app.schemas.transaction import TransactionCreate

from app.services.rabbitmq import RabbitMQClient
from app.services.redis_lock import acquire_locks, is_locked


class TaskRouter:
    def __init__(self, crud_users: CRUDUsers, crud_transactions: CRUDTransactions):
        self.crud_users = crud_users
        self.crud_transactions = crud_transactions
        self.handlers = {
            "get_users": self.handle_get_users,
            "register_user": self.handle_register_user,
            "create_transaction": self.create_transaction,
        }

    async def route(self, task_data: dict):
        task_type = task_data.get("task")
        data = task_data.get("data", {})

        handler = self.handlers.get(task_type)
        if not handler:
            logger.warning(f"Unknown task: {task_type}")
            return {"status": "error", "detail": "unknown task"}

        try:
            return await handler(data)
        except Exception as e:
            logger.error(f"Error handling task {task_type}: {e}")
            return {"status": "error", "detail": "internal error"}

    async def handle_get_users(self, _data):
        try:
            users = await self.crud_users.get_all_users()
            logger.info(f"Fetched {len(users)} users.")
            return {"users": [user.username for user in users]}
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return {"status": "error", "detail": "internal error"}

    async def handle_register_user(self, data: dict):
        user_create = UserCreate(**data)
        try:
            await self.crud_users.create_user(user_create.username, user_create.password)
            logger.info(f"User registered: {user_create.username}")
            return {"status": "success"}
        except IntegrityError:
            logger.error(f"Registration failed: username {user_create.username} already exists")
            return {"status": "error", "detail": "username already exists"}
        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}")
            return {"status": "error", "detail": "internal error"}

    async def create_transaction(self, data: dict):
        transaction = TransactionCreate(**data)
        if transaction.sender_id == transaction.receiver_id:
            return {"status": "error", "detail": "sender and receiver cannot be the same"}
        try:
            await self.crud_transactions.create_transaction(transaction)
            logger.info(f"Transaction created: {transaction.sender_id} -> {transaction.receiver_id}, Amount: {transaction.amount}")
            return {"status": "success"}
        except IntegrityError:
            logger.error(f"Transaction failed: insufficient funds or invalid user IDs")
            return {"status": "error", "detail": "insufficient funds or invalid user IDs"}
        except Exception as e:
            logger.error(f"Unexpected error during transaction creation: {e}")
            return {"status": "error", "detail": "internal error"}

def extract_user_ids(task_data: dict) -> list[int]:
    if task_data.get("task") == "create_transaction":
        data = task_data.get("data", {})
        user_ids = [data.get("sender_id"), data.get("receiver_id")]
        return [uid for uid in user_ids if uid is not None]
    return []

class Worker:
    def __init__(self, task_router: TaskRouter, rabbitmq_client: RabbitMQClient):
        self.task_router = task_router
        self.rabbitmq_client = rabbitmq_client
        self.queue = None 

    async def run(self):
        InitDB()

        await self.rabbitmq_client.connect()
        self.queue = await self.rabbitmq_client.channel.declare_queue(self.rabbitmq_client.queue_name, durable=True)

        logger.info("Worker started. Polling messages...")

        while True:
            try:
                message = await self.queue.get(no_ack=False)
            except aio_pika.exceptions.QueueEmpty:
                await asyncio.sleep(1)
                continue
            try:
                task_data = json.loads(message.body.decode())
                logger.info(f"Received task: {task_data}")

                user_ids = extract_user_ids(task_data)
                if task_data.get("task") == "create_transaction":
                    data = task_data.get("data", {})
                    if data.get("sender_id") == data.get("receiver_id"):
                        logger.info(f"Sender and receiver are the same ({data.get('sender_id')}), skipping task.")
                        await message.ack()
                        continue
                if user_ids:
                    locked = await is_locked(user_ids)
                    if locked:
                        logger.debug(f"Users {user_ids} locked. Requeuing message.")
                        await message.nack(requeue=True)
                        await asyncio.sleep(0.5)
                        continue

                async with acquire_locks(user_ids):
                    result = await self.task_router.route(task_data)

                logger.info(f"Task result: {result}")
                await message.ack()

            except Exception as e:
                logger.error(f"Error handling message: {e}")
                if message:
                    await message.ack()
                    await self.rabbitmq_client.send_message(message.body.decode())
                await asyncio.sleep(0.5)


if __name__ == "__main__":
    crud_users = CRUDUsers()
    crud_transactions = CRUDTransactions()
    rabbitmq = RabbitMQClient(amqp_url=RABBITMQ_URL, queue_name=QUEUE_NAME)
    router = TaskRouter(crud_users, crud_transactions)
    worker = Worker(router, rabbitmq)
    asyncio.run(worker.run())
