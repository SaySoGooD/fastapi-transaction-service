from pydantic import BaseModel


class UserData(BaseModel):
    username: str
    password: str
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True