from fastapi import Header, HTTPException, Request, status

from app.config import API_TOKEN
from app.database.crud import CRUDTransactions, CRUDUsers
from app.services.rabbitmq import RabbitMQClient

class Dependencies:
    def __init__(self):
        self.crud_users = CRUDUsers() # Переименовать в protected member
        self.crud_transactions = CRUDTransactions() # Переименовать в protected member

    # @staticmethod  Т.к. не используешь переменные из self
    async def verify_token(self, x_token: str = Header(...)): # typing.Annotated и description в Header
        # Также в хэдере указать alias = x-token (пишем не через _, а через - ). Также какой токен??? refresh/access/API
        """Dependency to verify API token."""
        if x_token != API_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Token"
            )

    async def get_crud_users(self):
        """Dependency to get CRUD instance for users."""
        return self.crud_users

    async def get_crud_transactions(self):
        """Dependency to get CRUD instance for transactions."""
        return self.crud_transactions

    def get_rabbitmq(self, request: Request) -> RabbitMQClient:
        return request.app.state.rabbitmq