from pydantic import BaseModel, Field

class TransactionCreate(BaseModel):
    sender_id: int
    receiver_id: int
    amount: float = Field(..., ge=0, description="Amount must be non-negative")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
