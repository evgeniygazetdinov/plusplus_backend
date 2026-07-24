import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from chat_volc.models.models import Message, PrivateChat, User
from chat_volc.settings import get_db

router = APIRouter(prefix="/users", tags=["Users"])


def _serialize_user(user: User) -> dict:
    return user.to_public_dict()


@router.get("/search")
async def search_users(
    q: str = Query(..., min_length=1),
    exclude_uid: str | None = None,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Поиск пользователей по имени или email."""
    term = q.strip()
    if not term:
        return {"status": "ok", "users": []}

    like = f"%{term}%"
    query = db.query(User).filter(
        or_(User.username.ilike(like), User.email.ilike(like))
    )
    if exclude_uid:
        query = query.filter(User.uid != exclude_uid)
    users = query.order_by(User.username.asc()).limit(limit).all()
    return {"status": "ok", "users": [_serialize_user(u) for u in users]}


@router.get("/{user_uid}/chats")
async def list_user_chats(user_uid: str, db: Session = Depends(get_db)):
    """Список приватных чатов пользователя с собеседником и последним сообщением."""
    user = db.query(User).filter(User.uid == user_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chats = (
        db.query(PrivateChat)
        .filter(
            or_(
                PrivateChat.user_one_id == user.id,
                PrivateChat.user_two_id == user.id,
            )
        )
        .all()
    )

    result = []
    for chat in chats:
        peer_id = chat.user_two_id if chat.user_one_id == user.id else chat.user_one_id
        peer = db.query(User).filter(User.id == peer_id).first()
        last_message = (
            db.query(Message)
            .options(joinedload(Message.user))
            .filter(Message.chat_id == chat.id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .first()
        )
        result.append(
            {
                "id": chat.id,
                "peer": peer.to_public_dict() if peer else None,
                "last_message": last_message.to_dict() if last_message else None,
            }
        )

    result.sort(
        key=lambda item: (
            item["last_message"]["created_at"]
            if item["last_message"] and item["last_message"].get("created_at")
            else ""
        ),
        reverse=True,
    )
    return {"status": "ok", "chats": result}


@router.get("/last_five_users")
async def last_five_users(db: Session = Depends(get_db), username: str = None):
    users = db.query(User).all()[-5:]
    return {"status": "ok", "users": [_serialize_user(u) for u in users]}


@router.post("/")
async def create_user(
    request: Request,
    db: Session = Depends(get_db),
    username: str = None,
    email: str | None = None,
):
    if request.method == "POST":
        new_user = User(
            uid=str(uuid.uuid4()),
            username=username or "user",
            email=email,
            provider="local",
            provider_id=str(uuid.uuid4()),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"status": "User created", "user": _serialize_user(new_user)}

    raise HTTPException(status_code=405, detail="Method not allowed")


@router.get("/{user_id}")
async def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize_user(user)


@router.delete("/{user_id}")
async def delete_user(request: Request, user_id: str, db: Session = Depends(get_db)):
    if request.method == "DELETE":
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        db.delete(user)
        db.commit()
        return {"status": "User deleted"}

    raise HTTPException(status_code=405, detail="Method not allowed")
