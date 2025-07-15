from pydantic import BaseModel


class TransactionCreate(BaseModel):
    sender_id: int
    receiver_id: int
    amount: float # Добавить валидацию на отрицательные числа
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
