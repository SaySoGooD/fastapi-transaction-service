from decimal import Decimal
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Transaction, User
from app.schemas.transaction import TransactionCreate


class CRUDUsers:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        user = await self.session.execute(select(User).where(User.id == user_id))
        return user.scalar_one_or_none()
    
    async def get_user_by_data(self, username: str, password: str) -> User | None:
        user = await self.session.execute(select(User).where(User.username == username,
                                                             User.password == password))
        return user.scalar_one_or_none()

    async def create_user(self, username: str, password: str) -> User:
        user = User(username=username, password=password)
        self.session.add(user)
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise e
        await self.session.refresh(user)
        return user

    async def get_total_sent_amount(self, user_id: int) -> float:
        result = await self.session.execute(
            select(func.sum(Transaction.amount)).where(Transaction.sender_id == user_id)
        )
        return result.scalar() or 0

    async def get_all_users(self) -> Sequence[User]:
        result = await self.session.execute(select(User))
        return result.scalars().all()
    

class CRUDTransactions:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_transaction(self, transaction: TransactionCreate) -> None:
        async with self.session.begin():
            sender = await self.session.get(User, transaction.sender_id, with_for_update=True)
            receiver = await self.session.get(User, transaction.receiver_id, with_for_update=True)
            try:
                if not sender or not receiver:
                    raise ValueError("Sender or receiver does not exist")
                amount = Decimal(str(transaction.amount))
                if sender.balance < amount:
                    raise ValueError("Insufficient balance")
                sender.balance -= amount
                receiver.balance += amount
                new_transaction = Transaction(
                    sender_id=transaction.sender_id,
                    receiver_id=transaction.receiver_id,
                    amount=transaction.amount
                )
                self.session.add(new_transaction)
                await self.session.commit()
            except Exception as e:
                await self.session.rollback()
                raise e

    async def get_transactions_by_user(self, user_id: int) -> Sequence[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(
                (Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)
            )
            )
        return result.scalars().all()