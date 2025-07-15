import json

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.api.dependencies import Dependencies
from app.database.crud import CRUDUsers
from app.schemas.transaction import TransactionCreate
from app.schemas.user import UserCreate
from app.services.rabbitmq import RabbitMQClient

main_router = APIRouter()
dependencies = Dependencies()

@main_router.get("/users", tags=["Users"])
async def get_all_users_handler(crud: CRUDUsers = Depends(dependencies.get_crud_users),
                                 _ = Depends(dependencies.verify_token)):
    """Fetch all users from the database."""
    try:
        users = await crud.get_all_users()
        return {"users": [user.username for user in users]}
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users"
        )


@main_router.post("/registration", tags=["Users"])
async def register_user_handler(user: UserCreate, 
                                rabbitmq_client: RabbitMQClient = Depends(dependencies.get_rabbitmq),
                                _=Depends(dependencies.verify_token)):
    """Registers a new user."""
    try:
        task = {
            "task": "register_user",
            "data": user.dict()
        }
        await rabbitmq_client.send_message(json.dumps(task))
        return {"message": "User registration task queued."}
    except Exception as e:
        logger.error(f"Error sending registration to queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue registration task."
        )
    

@main_router.post("/new-transaction", tags=["Transactions"])
async def create_transaction_handler(transaction: TransactionCreate, 
                                     rabbitmq_client: RabbitMQClient = Depends(dependencies.get_rabbitmq),
                                     _=Depends(dependencies.verify_token)):
    """Creates a new transaction."""
    if transaction.sender_id == transaction.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sender and receiver cannot be the same."
        )
    try:
        task = {
            "task": "create_transaction",
            "data": transaction.dict()
        }
        await rabbitmq_client.send_message(json.dumps(task))
        return {"message": "Transaction queued."}
    except Exception as e:
        logger.error(f"Error queuing transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue transaction."
        )