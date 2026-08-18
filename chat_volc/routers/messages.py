from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload

from chat_volc.auth import get_current_user
from chat_volc.chat_access import get_chat_for_member
from chat_volc.models.models import Message, User
from chat_volc.models.schemas import MessageCreate
from chat_volc.settings import get_db

router = APIRouter(prefix="/private_chat/{private_chat_id}", tags=["messages"])


@router.post("/message")
async def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    private_chat_id: str = "",
    current_user: User = Depends(get_current_user),
):
    get_chat_for_member(db, private_chat_id, current_user)

    try:
        new_message = Message.create_message(
            db=db,
            private_chat_id=private_chat_id,
            data=type("Data", (), {"user_id": current_user.uid, "text": message_data.text})(),
        )
    except Exception:
        raise HTTPException(status_code=404, detail="chat or user not found")

    return {
        "status": "Message created",
        "new_message": new_message.to_dict(),
    }


@router.get("/{message_id}")
async def get_message_by_id(
    message_id: str,
    db: Session = Depends(get_db),
    private_chat_id: str = "",
    current_user: User = Depends(get_current_user),
):
    get_chat_for_member(db, private_chat_id, current_user)
    message = db.query(Message).filter(Message.id == message_id).first()
    if message:
        return message
    raise HTTPException(status_code=404, detail="Message not found")


@router.delete("/{message_id}")
async def delete_message_by_id(
    message_id: str,
    db: Session = Depends(get_db),
    private_chat_id: str = "",
    current_user: User = Depends(get_current_user),
):
    get_chat_for_member(db, private_chat_id, current_user)
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(message)
    db.commit()
    return {"status": "Message deleted"}
