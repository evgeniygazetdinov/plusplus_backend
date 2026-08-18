from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload

from chat_volc.auth import get_current_user
from chat_volc.chat_access import get_chat_for_member
from chat_volc.models.models import User, PrivateChat, ChatAlreadyExistsError, Message
from chat_volc.models.schemas import PrivateChatCreate
from chat_volc.settings import get_db

router = APIRouter(prefix="/private_chat", tags=["PrivateChats"])


@router.post("/")
async def create_chat(
    chat_data: PrivateChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_one = db.query(User).filter(User.uid == chat_data.user_one_uid).first()
    user_two = db.query(User).filter(User.uid == chat_data.user_two_uid).first()

    if not user_one or not user_two:
        raise HTTPException(status_code=404, detail="one of users not found")

    if user_one.id == user_two.id:
        raise HTTPException(status_code=400, detail="cannot create chat with yourself")

    if current_user.id not in (user_one.id, user_two.id):
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        new_chat = PrivateChat.create_chat(db, user_one.id, user_two.id)
    except ChatAlreadyExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(exc),
                "chat_id": exc.chat.id,
            },
        )

    return {"status": "private Chat created", "new_chat": {"id": new_chat.id}}


@router.get("/{private_chat_id}")
async def get_chat(
    private_chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    private_chat = get_chat_for_member(db, private_chat_id, current_user)
    return {
        "id": private_chat.id,
        "user_one_id": private_chat.user_one_id,
        "user_two_id": private_chat.user_two_id,
    }


@router.get("/{private_chat_id}/all_messages")
async def get_all_chat_messages(
    private_chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    private_chat = get_chat_for_member(db, private_chat_id, current_user)

    messages = (
        db.query(Message)
        .options(joinedload(Message.user))
        .filter(Message.chat_id == private_chat.id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )
    return [m.to_dict() for m in messages]


@router.delete("/{private_chat_id}")
async def delete_chat(
    private_chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    private_chat = get_chat_for_member(db, private_chat_id, current_user)
    db.delete(private_chat)
    db.commit()
    return {"status": "private_chat deleted"}
