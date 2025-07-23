from typing import Annotated
from fastapi import Header, HTTPException, Request

from app.config import settings
from app.database.crud import CRUDTransactions, CRUDUsers
from app.database.database import AsyncSessionManager
from app.services.rabbitmq import RabbitMQClient

class Dependencies:
    def __init__(self):
        session_manager = AsyncSessionManager()
        session = session_manager.get_session()
        self._crud_users = CRUDUsers(session)
        self._crud_transactions = CRUDTransactions(session)


    @staticmethod
    async def verify_token(
        x_token: Annotated[
            str,
            Header(
                alias="x-token",
                description="Access token for API authentication"
            )
        ]
    ):
        """Dependency to verify API access token."""
        if x_token != settings.api.token:
            raise HTTPException(status_code=403, detail="Invalid token")

    async def get_crud_users(self):
        """Dependency to get CRUD instance for users."""
        return self._crud_users

    async def get_crud_transactions(self):
        """Dependency to get CRUD instance for transactions."""
        return self._crud_transactions

    async def get_rabbitmq(self, request: Request) -> RabbitMQClient:
        return request.app.state.rabbitmq