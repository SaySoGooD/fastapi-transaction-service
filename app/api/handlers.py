from typing_extensions import Annotated
import orjson

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.api.dependencies import Dependencies
from app.database.crud import CRUDUsers
from app.schemas.transaction import TransactionCreate
from app.schemas.user import UserData
from app.services.rabbitmq import rabbitmq


main_router = APIRouter()
dependencies = Dependencies()


@main_router.get("/users", 
                 tags=["Users"], 
                 dependencies=[Depends(dependencies.verify_token)])
async def get_all_users_handler(crud: Annotated[CRUDUsers, Depends(dependencies.get_crud_users)])->dict:
    """Fetch all users from the database."""
    try:
        users = await crud.get_all_users()
        return {"users": [[user.id, user.username] for user in users]}
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users"
        )


@main_router.post("/registration", 
                  tags=["Users"],
                  dependencies=[Depends(dependencies.verify_token)])
async def register_user_handler(user: Annotated[UserData, 'Login and password for new user'], 
                                crud: Annotated[CRUDUsers, Depends(dependencies.get_crud_users)]):
    """Registers a new user."""
    try:
        res = await crud.create_user(username=user.username, password=user.password)
        return {'status': "SUCCES", "key": res}
    except Exception as e:
        logger.error(f"Error registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed registration."
        )


@main_router.post("/login",
                  tags=['Users'],
                  dependencies=[Depends(dependencies.verify_token)])
async def login_user_handler(user: Annotated[UserData, "Login and password for identification"],
                             crud: Annotated[CRUDUsers, Depends(dependencies.get_crud_users)]):
    """Auth user process"""
    try:
        res = await crud.get_user_by_data(username=user.username, password=user.password)
        return {'status': "SUCCES", "key": res}
    except Exception as e:
        logger.debug(f"Failed login: {user.username, len(user.password)*'*'}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed login. Bad login or password"
        )


@main_router.post("/new-transaction", 
                  tags=["Transactions"],
                  dependencies=[Depends(dependencies.verify_token)])
async def create_transaction_handler(transaction: Annotated[TransactionCreate, 'Transaction data']):
    """Creates a new transaction."""
    if transaction.sender_id == transaction.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't send money to yourself"
        )
    try:
        task = {
            "task": "create_transaction",
            "data": transaction.model_dump()
        }
        await rabbitmq.send_message(orjson.dumps(task).decode("utf-8"))
        return {"message": "Transaction queued."}
    except Exception as e:
        logger.error(f"Error queuing transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue transaction."
        )