import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from chat_volc.models.models import User
from chat_volc.settings import get_db

JWT_SECRET = os.getenv("JWT_SECRET", "chat-volc-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "30"))
ALLOW_DEV_AUTH = os.getenv("ALLOW_DEV_AUTH", "1") in ("1", "true", "True", "yes")

_bearer = HTTPBearer(auto_error=False)


def create_access_token(user: User) -> str:
    payload = {
        "sub": user.uid,
        "uid": user.uid,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
    uid = payload.get("uid") or payload.get("sub")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    return uid


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    uid = decode_access_token(credentials.credentials)
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


async def fetch_yandex_profile(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://login.yandex.ru/info",
            params={"format": "json"},
            headers={"Authorization": f"OAuth {access_token}"},
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Yandex access token",
        )
    data = response.json()
    email = data.get("default_email") or (data.get("emails") or [None])[0]
    display_name = (
        data.get("display_name")
        or data.get("real_name")
        or data.get("login")
        or (email.split("@")[0] if email else "Яндекс")
    )
    provider_id = str(data.get("id") or data.get("psuid") or "")
    if not provider_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yandex profile missing id",
        )
    avatar_url = None
    if data.get("default_avatar_id"):
        avatar_url = (
            f"https://avatars.yandex.net/get-yapic/{data['default_avatar_id']}/islands-200"
        )
    return {
        "provider": "yandex",
        "provider_id": provider_id,
        "email": email,
        "username": display_name,
        "avatar_url": avatar_url,
    }


async def fetch_vk_profile(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        user_resp = await client.get(
            "https://api.vk.com/method/users.get",
            params={
                "access_token": access_token,
                "v": "5.199",
                "fields": "photo_200,screen_name",
            },
        )
        email_resp = await client.get(
            "https://api.vk.com/method/account.getProfileInfo",
            params={"access_token": access_token, "v": "5.199"},
        )
    user_payload = user_resp.json()
    if "error" in user_payload or not user_payload.get("response"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid VK access token",
        )
    profile = user_payload["response"][0]
    provider_id = str(profile["id"])
    first = profile.get("first_name") or ""
    last = profile.get("last_name") or ""
    username = (f"{first} {last}").strip() or profile.get("screen_name") or f"vk_{provider_id}"
    email = None
    email_payload = email_resp.json()
    if "response" in email_payload:
        email = email_payload["response"].get("email") or email_payload["response"].get(
            "screen_name"
        )
    # Implicit flow can put email in token response; client may pass it separately later.
    if not email:
        email = f"vk_{provider_id}@vk.local"
    return {
        "provider": "vk",
        "provider_id": provider_id,
        "email": email,
        "username": username,
        "avatar_url": profile.get("photo_200"),
    }


async def resolve_oauth_profile(provider: str, access_token: str) -> dict:
    if provider == "yandex":
        return await fetch_yandex_profile(access_token)
    if provider == "vk":
        return await fetch_vk_profile(access_token)
    raise HTTPException(status_code=400, detail="Unsupported provider")


def upsert_oauth_user(db: Session, profile: dict) -> User:
    user = (
        db.query(User)
        .filter(
            User.provider == profile["provider"],
            User.provider_id == profile["provider_id"],
        )
        .first()
    )
    if user is None and profile.get("email"):
        user = db.query(User).filter(User.email == profile["email"]).first()

    if user is None:
        user = User(
            uid=str(__import__("uuid").uuid4()),
            username=profile["username"],
            email=profile.get("email"),
            provider=profile["provider"],
            provider_id=profile["provider_id"],
            avatar_url=profile.get("avatar_url"),
        )
        db.add(user)
    else:
        user.username = profile["username"] or user.username
        user.email = profile.get("email") or user.email
        user.provider = profile["provider"]
        user.provider_id = profile["provider_id"]
        user.avatar_url = profile.get("avatar_url") or user.avatar_url

    db.commit()
    db.refresh(user)
    return user
