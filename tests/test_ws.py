"""WebSocket tests — используем TestClient (sync over ASGI)."""
import json

import pytest
from starlette.websockets import WebSocketDisconnect

from chat_volc.auth import create_access_token


def _token(user) -> str:
    return create_access_token(user)


def test_ws_requires_token(client, chat):
    private_chat, _, _ = chat
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws/chat/{private_chat.id}"):
            pass
    assert exc.value.code == 1008


def test_ws_rejects_invalid_token(client, chat):
    private_chat, _, _ = chat
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            f"/ws/chat/{private_chat.id}?token=bad.token.here"
        ):
            pass
    assert exc.value.code == 1008


def test_ws_rejects_non_participant(client, chat, make_user):
    private_chat, _, _ = chat
    outsider = make_user("outsider_ws")
    token = _token(outsider)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            f"/ws/chat/{private_chat.id}?token={token}"
        ):
            pass
    assert exc.value.code == 1008


def test_ws_ping_pong(client, chat):
    private_chat, user_one, _ = chat
    token = _token(user_one)
    with client.websocket_connect(f"/ws/chat/{private_chat.id}?token={token}") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        data = ws.receive_json()
        assert data["type"] == "pong"


def test_ws_send_message(client, chat):
    private_chat, user_one, _ = chat
    token = _token(user_one)
    with client.websocket_connect(f"/ws/chat/{private_chat.id}?token={token}") as ws:
        ws.send_text(json.dumps({"type": "message", "text": "hello ws"}))
        data = ws.receive_json()
        assert data["type"] == "message"
        assert data["text"] == "hello ws"
        assert data["user_uid"] == user_one.uid


def test_ws_send_empty_message_is_error(client, chat):
    private_chat, user_one, _ = chat
    token = _token(user_one)
    with client.websocket_connect(f"/ws/chat/{private_chat.id}?token={token}") as ws:
        ws.send_text(json.dumps({"type": "message", "text": "  "}))
        data = ws.receive_json()
        assert data["type"] == "error"
