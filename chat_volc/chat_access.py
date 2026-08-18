from fastapi import HTTPException
from sqlalchemy.orm import Session

from chat_volc.models.models import PrivateChat, User


def get_chat_for_member(db: Session, private_chat_id: str | int, user: User) -> PrivateChat:
    private_chat = (
        db.query(PrivateChat).filter(PrivateChat.id == private_chat_id).first()
    )
    if not private_chat:
        raise HTTPException(status_code=404, detail="private_chat not found")
    if user.id not in (private_chat.user_one_id, private_chat.user_two_id):
        raise HTTPException(status_code=403, detail="Not a chat participant")
    return private_chat
