from decimal import Decimal
from typing import List

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    sent_transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="sender",
        foreign_keys="[Transaction.sender_id]",
    )
    received_transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="receiver",
        foreign_keys="[Transaction.receiver_id]",
    )

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))

    sender: Mapped[User] = relationship(
        back_populates="sent_transactions",
        foreign_keys=[sender_id]
    )
    receiver: Mapped[User] = relationship(
        back_populates="received_transactions",
        foreign_keys=[receiver_id]
    )   
