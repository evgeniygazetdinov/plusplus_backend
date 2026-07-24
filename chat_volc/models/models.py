from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship, joinedload
from datetime import datetime

import uuid
from chat_volc.settings import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("provider", "provider_id", name="uix_provider_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, index=True)
    email = Column(String, index=True, nullable=True)
    password_hash = Column(String, nullable=True)
    provider = Column(String, nullable=True, index=True)  # yandex | vk | google | local
    provider_id = Column(String, nullable=True, index=True)
    avatar_url = Column(String, nullable=True)

    def __repr__(self):
        return f"<User(uid='{self.uid}', username='{self.username}', email='{self.email}')>"

    def to_public_dict(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "username": self.username,
            "email": self.email,
            "provider": self.provider,
            "avatar_url": self.avatar_url,
        }


class ChatAlreadyExistsError(Exception):
    def __init__(self, chat):
        self.chat = chat
        super().__init__("Chat already exists between these two users.")


class PrivateChat(Base):
    __tablename__ = "private_chats"

    id = Column(Integer, primary_key=True, index=True)
    user_one_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_two_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    messages = relationship("Message", back_populates="chat")

    def create_chat(db, user_one_id, user_two_id):
        existing_chat = (
            db.query(PrivateChat)
            .filter(
                (
                    (PrivateChat.user_one_id == user_one_id)
                    & (PrivateChat.user_two_id == user_two_id)
                )
                | (
                    (PrivateChat.user_one_id == user_two_id)
                    & (PrivateChat.user_two_id == user_one_id)
                )
            )
            .first()
        )

        if existing_chat:
            raise ChatAlreadyExistsError(existing_chat)

        new_chat = PrivateChat(user_one_id=user_one_id, user_two_id=user_two_id)
        db.add(new_chat)
        db.commit()
        return new_chat


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("private_chats.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    emotion = Column(String, nullable=True)
    chat = relationship("PrivateChat", back_populates="messages")
    user = relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "user_uid": self.user.uid if self.user else None,
            "username": self.user.username if self.user else None,
            "text": self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "emotion": self.emotion,
        }

    @staticmethod
    def create_message(db, private_chat_id, data):
        text = data.text
        user = db.query(User).filter(User.uid == data.user_id).first()
        current_chat = db.query(PrivateChat).filter(PrivateChat.id == private_chat_id)
        chat_exists = db.query(current_chat.exists()).scalar()

        if not chat_exists or not user:
            raise Exception("chat or user id not exists")

        user_id = user.id
        private_chat = current_chat.first()
        chat_users = [private_chat.user_one_id, private_chat.user_two_id]
        if user_id not in chat_users:
            raise Exception("chat or user id not exists")

        new_message = Message(
            chat_id=private_chat_id,
            user_id=user_id,
            text=text,
            created_at=datetime.now(),
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        new_message = (
            db.query(Message)
            .options(joinedload(Message.user))
            .filter(Message.id == new_message.id)
            .first()
        )
        return new_message
