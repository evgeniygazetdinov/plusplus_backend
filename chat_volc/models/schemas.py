from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Literal


class UserCreate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uid: str
    username: str
    email: Optional[str] = None
    provider: Optional[str] = None
    avatar_url: Optional[str] = None


class OAuthLoginRequest(BaseModel):
    provider: Literal["yandex", "vk", "google"]
    access_token: str


class DevLoginRequest(BaseModel):
    """Локальный вход без OAuth (только если ALLOW_DEV_AUTH=1)."""

    provider: Literal["yandex", "vk", "google"] = "yandex"
    email: str
    username: str = Field(min_length=1, max_length=100)


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6, max_length=128)
    username: str = Field(min_length=1, max_length=100)


class PasswordLoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    status: str = "ok"
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PrivateChatBase(BaseModel):
    user_one_uid: str
    user_two_uid: str


class PrivateChatCreate(BaseModel):
    user_one_uid: str
    user_two_uid: str


class PrivateChat(PrivateChatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    messages: List[int]


class MessageCreate(BaseModel):
    user_id: str
    text: str


class MessageBase(BaseModel):
    user_id: int
    text: str


class Message(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
