from decimal import Decimal

from sqlalchemy import func, select

from app.database.database import AsyncSessionManager
from app.database.models import Transaction, User
from app.schemas.transaction import TransactionCreate


class CRUDUsers:
    def __init__(self):
        self._db = AsyncSessionManager() # Класс должен получать уже готовую сессиию, а не их генератор(искл: бд SQLite)

    async def get_user_by_id(self, user_id: int) -> User | None:
        async with self._db.get_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    async def create_user(self, username: str, password: str) -> User:
        user = User(username=username, password=password)
        async with self._db.get_session() as session:
            session.add(user)
            try:
                await session.commit()
            except Exception as e: # e - unused
                await session.rollback()
                raise # raise e
            await session.refresh(user)
        return user

    async def get_total_sent_amount(self, user_id: int) -> float:
        async with self._db.get_session() as session:
            result = await session.execute(
                select(func.sum(Transaction.amount)).where(Transaction.sender_id == user_id)
        )
        return result.scalar() or 0

    async def get_all_users(self) -> list[User]:
        async with self._db.get_session() as session:
            result = await session.execute(select(User))
        return result.scalars().all()
    

class CRUDTransactions:
    def __init__(self):
        self._db = AsyncSessionManager()

    async def create_transaction(self, transaction: TransactionCreate) -> Transaction:
        async with self._db.get_session() as session:
            async with session.begin():
                sender = await session.get(User, transaction.sender_id, with_for_update=True)
                receiver = await session.get(User, transaction.receiver_id, with_for_update=True)
                amount = Decimal(str(transaction.amount)) # Круто
                sender.balance -= amount
                receiver.balance += amount

                new_transaction = Transaction(
                    sender_id=transaction.sender_id,
                    receiver_id=transaction.receiver_id,
                    amount=transaction.amount
                )
                session.add(new_transaction)
                await session.commit()

    async def get_transactions_by_user(self, user_id: int) -> list[Transaction]:
        async with self._db.get_session() as session:
            result = await session.execute(
                select(Transaction).where(
                    (Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)
                )
            )
        return result.scalars().all()