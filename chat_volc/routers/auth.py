import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from chat_volc.auth import (
    ALLOW_DEV_AUTH,
    create_access_token,
    get_current_user,
    hash_password,
    resolve_oauth_profile,
    upsert_oauth_user,
    verify_password,
)
from chat_volc.models.models import User
from chat_volc.models.schemas import (
    AuthResponse,
    DevLoginRequest,
    OAuthLoginRequest,
    PasswordLoginRequest,
    RegisterRequest,
)
from chat_volc.settings import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


def _auth_payload(user: User) -> dict:
    return {
        "status": "ok",
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user.to_public_dict(),
    }


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username required")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        uid=str(uuid.uuid4()),
        username=username,
        email=email,
        password_hash=hash_password(body.password),
        provider="local",
        provider_id=f"local:{email}",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _auth_payload(user)


@router.post("/login", response_model=AuthResponse)
async def password_login(body: PasswordLoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    return _auth_payload(user)


@router.post("/oauth", response_model=AuthResponse)
async def oauth_login(body: OAuthLoginRequest, db: Session = Depends(get_db)):
    profile = await resolve_oauth_profile(body.provider, body.access_token)
    user = upsert_oauth_user(db, profile)
    return _auth_payload(user)


@router.post("/dev", response_model=AuthResponse)
async def dev_login(body: DevLoginRequest, db: Session = Depends(get_db)):
    """Вход по email без пароля — только для локальной разработки."""
    if not ALLOW_DEV_AUTH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev auth is disabled",
        )
    email = body.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

    provider_id = f"dev:{email}"
    profile = {
        "provider": body.provider,
        "provider_id": provider_id,
        "email": email,
        "username": body.username.strip(),
        "avatar_url": None,
    }
    user = upsert_oauth_user(db, profile)
    return _auth_payload(user)


@router.get("/me")
async def auth_me(user: User = Depends(get_current_user)):
    return {"status": "ok", "user": user.to_public_dict()}
