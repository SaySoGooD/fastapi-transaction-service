import json # Слишком медленный, лучше использовать orjson(скорость 50x)

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.api.dependencies import Dependencies
from app.database.crud import CRUDUsers
from app.schemas.transaction import TransactionCreate
from app.schemas.user import UserCreate
from app.services.rabbitmq import RabbitMQClient

main_router = APIRouter()
dependencies = Dependencies()

# Вопросы к коду:
# 1. Как пользователи узнают о своем ID? /users - очень нагружает бд
# 2. Как система узнает пользователей => сделать сессионные/jwt токен, а проще взять готовый сервис аунтентификации/авторизации и public_key для проверки подписи токенов
# Можешь взять какие-нибудь другие решения, но вот мой https://github.com/mrzkv/LinkAly/tree/main/AuthenticationService


@main_router.get(
    path="/users",
    tags=["Users"],
    # dependencies=[dependencies.verify_token], а лучше вынести в мидлварь
)
async def get_all_users_handler(crud: CRUDUsers = Depends(dependencies.get_crud_users), # В FastAPI мы используем typing.Anotated
                                # т.е. вот так crud: Annotated[CRUDUsers, Depends(dependencies.get_crud_users)]
                                 _ = Depends(dependencies.verify_token)): # Убрать
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

    # Здесь кроль оверкилл.
    try:
        task = {
            "task": "register_user",
            "data": user.dict() # .dict - депрекейтед
        }
        await rabbitmq_client.send_message(json.dumps(task)) # json -> orjson
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
            detail="Sender and receiver cannot be the same." # Может лучше "You cant send money to yourself"
        )
    try:
        task = {
            "task": "create_transaction",
            "data": transaction.dict() # .dict - депрекейтед, используем .model_dump()
        }
        await rabbitmq_client.send_message(json.dumps(task)) # уже говорил лучше orjson
        return {"message": "Transaction queued."}
    except Exception as e:
        logger.error(f"Error queuing transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue transaction."
        )