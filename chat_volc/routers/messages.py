from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from chat_volc.models.models import PrivateChat, Message, User
from chat_volc.models.schemas import MessageCreate
from chat_volc.settings import get_db

router = APIRouter(prefix="/private_chat/{private_chat_id}", tags=["messages"])


@router.post("/message")
async def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    private_chat_id: str = "",
):
    try:
        new_message = Message.create_message(
            db=db, private_chat_id=private_chat_id, data=message_data
        )
    except Exception:
        raise HTTPException(status_code=404, detail="chat or user not found")

    return {
        "status": "Message created",
        "new_message": {"id": new_message.id, "text": new_message.text},
    }


@router.get("/{message_id}")
async def get_message_by_id(
    request: Request, message_id: str, db: Session = Depends(get_db)
):
    if request.method == "GET":
        message = db.query(Message).filter(Message.id == message_id).first()
        if message:
            return message
        raise HTTPException(status_code=404, detail="Message not found")


@router.delete("/{message_id}")
async def delete_message_by_id(
    request: Request, message_id: str, db: Session = Depends(get_db)
):
    if request.method == "DELETE":
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        db.delete(message)
        db.commit()
        return {"status": "Message deleted"}

    raise HTTPException(status_code=405, detail="Method not allowed")
