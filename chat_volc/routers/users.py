import uuid

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from chat_volc.models.models import User
from chat_volc.settings import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/last_five_users")
async def last_five_users(db: Session = Depends(get_db), username: str = None):
    users = db.query(User).all()[-5:]
    return {"status": "ok", "users": users}


@router.post("/")
async def create_user(
    request: Request, db: Session = Depends(get_db), username: str = None
):
    if request.method == "POST":
        new_user = User(uid=str(uuid.uuid4()), username=username)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"status": "User created", "user": new_user}

    raise HTTPException(status_code=405, detail="Method not allowed")


@router.get("/{user_id}")
async def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


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
