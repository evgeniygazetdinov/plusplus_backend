"""
WebSocket-эндпоинт /ws/chat/{chat_id}

Протокол (JSON):
  клиент → сервер:
    {"type": "ping"}
    {"type": "message", "text": "..."}

  сервер → клиент:
    {"type": "pong"}
    {"type": "message",  ...поля ChatMessage...}
    {"type": "error",    "detail": "..."}

Redis pub/sub: канал  chat:{chat_id}
"""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from chat_volc.auth import decode_access_token
from chat_volc.chat_access import get_chat_for_member
from chat_volc.models.models import Message, User
from chat_volc.settings import REDIS_URL, get_db

log = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

# --------------------------------------------------------------------------- #
# ConnectionManager — локальные соединения текущего процесса
# --------------------------------------------------------------------------- #

class ConnectionManager:
    def __init__(self):
        # chat_id → set[WebSocket]
        self._rooms: dict[int, set[WebSocket]] = {}

    def add(self, chat_id: int, ws: WebSocket) -> None:
        self._rooms.setdefault(chat_id, set()).add(ws)

    def remove(self, chat_id: int, ws: WebSocket) -> None:
        room = self._rooms.get(chat_id)
        if room:
            room.discard(ws)
            if not room:
                del self._rooms[chat_id]

    async def broadcast_local(self, chat_id: int, payload: dict) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        dead: list[WebSocket] = []
        for ws in list(self._rooms.get(chat_id, [])):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.remove(chat_id, ws)


manager = ConnectionManager()


# --------------------------------------------------------------------------- #
# Redis subscriber (запускается один раз через lifespan)
# --------------------------------------------------------------------------- #

_subscriber_task: asyncio.Task | None = None


async def _redis_subscriber() -> None:
    """Слушает все каналы Redis chat:* и рассылает локальным сокетам."""
    import redis.asyncio as aioredis

    while True:
        try:
            r = aioredis.from_url(REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.psubscribe("chat:*")
            async for raw in pubsub.listen():
                if raw["type"] != "pmessage":
                    continue
                channel: str = raw["channel"]           # "chat:42"
                try:
                    chat_id = int(channel.split(":", 1)[1])
                    payload = json.loads(raw["data"])
                    await manager.broadcast_local(chat_id, payload)
                except Exception as exc:
                    log.warning("ws subscriber error: %s", exc)
        except Exception as exc:
            log.warning("Redis subscriber disconnected (%s), retry in 3s", exc)
            await asyncio.sleep(3)


def start_subscriber() -> None:
    global _subscriber_task
    if _subscriber_task is None or _subscriber_task.done():
        _subscriber_task = asyncio.create_task(_redis_subscriber())


# --------------------------------------------------------------------------- #
# Вспомогательная: публикация в Redis
# --------------------------------------------------------------------------- #

async def _publish(chat_id: int, payload: dict) -> None:
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        await r.publish(f"chat:{chat_id}", json.dumps(payload, ensure_ascii=False))
        await r.aclose()
    except Exception as exc:
        # Если Redis недоступен — рассылаем только локально
        log.warning("Redis publish failed: %s", exc)
        await manager.broadcast_local(chat_id, payload)


# --------------------------------------------------------------------------- #
# WebSocket endpoint
# --------------------------------------------------------------------------- #

@router.websocket("/ws/chat/{chat_id}")
async def chat_ws(
    chat_id: int,
    websocket: WebSocket,
    token: str = "",
    db: Session = Depends(get_db),
):
    # --- аутентификация ---
    token = token or websocket.query_params.get("token", "")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        uid = decode_access_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        get_chat_for_member(db, chat_id, user)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    manager.add(chat_id, websocket)

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                # keepalive
                await websocket.send_text(json.dumps({"type": "ping"}))
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid JSON"}))
                continue

            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            elif msg_type == "message":
                text = (data.get("text") or "").strip()
                if not text:
                    await websocket.send_text(json.dumps({"type": "error", "detail": "Empty text"}))
                    continue
                try:
                    new_msg = Message.create_message(
                        db,
                        chat_id,
                        type("D", (), {"user_id": user.uid, "text": text})(),
                    )
                    payload = {"type": "message", **new_msg.to_dict()}
                    await _publish(chat_id, payload)
                except Exception as exc:
                    await websocket.send_text(json.dumps({"type": "error", "detail": str(exc)}))

            else:
                await websocket.send_text(json.dumps({"type": "error", "detail": f"Unknown type: {msg_type}"}))

    except WebSocketDisconnect:
        pass
    finally:
        manager.remove(chat_id, websocket)
