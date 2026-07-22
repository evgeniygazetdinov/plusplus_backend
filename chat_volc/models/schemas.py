from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class UserCreate(BaseModel):
    user_id: Optional[int] = None
    # email: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class PrivateChatBase(BaseModel):
    user_one_uid: str
    user_two_uid: str


class PrivateChatCreate(BaseModel):
    user_one_uid: str
    user_two_uid: str


class PrivateChat(PrivateChatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    messages: List[int]  # Список идентификаторов сообщений, связанных с чатом


class MessageCreate(BaseModel):
    user_id: str
    text: str


class MessageBase(BaseModel):
    user_id: int
    text: str


class Message(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
