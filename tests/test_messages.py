from chat_volc.models.models import Message


def test_create_message_success(client, chat, auth_headers):
    private_chat, user_one, _ = chat

    response = client.post(
        f"/private_chat/{private_chat.id}/message",
        json={"text": "hello"},
        headers=auth_headers(user_one),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Message created"
    assert data["new_message"]["text"] == "hello"
    assert data["new_message"]["user_uid"] == user_one.uid
    assert "id" in data["new_message"]


def test_create_message_uses_jwt_not_body_user(client, chat, auth_headers):
    private_chat, user_one, user_two = chat

    response = client.post(
        f"/private_chat/{private_chat.id}/message",
        json={"text": "from bob"},
        headers=auth_headers(user_two),
    )

    assert response.status_code == 200
    assert response.json()["new_message"]["user_uid"] == user_two.uid


def test_create_message_requires_auth(client, chat):
    private_chat, _, _ = chat

    response = client.post(
        f"/private_chat/{private_chat.id}/message",
        json={"text": "hello"},
    )

    assert response.status_code == 401


def test_create_message_chat_not_found(client, make_user, auth_headers):
    user = make_user("orphan")

    response = client.post(
        "/private_chat/9999/message",
        json={"text": "hello"},
        headers=auth_headers(user),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "private_chat not found"


def test_create_message_forbidden_for_outsider(client, chat, make_user, auth_headers):
    private_chat, _, _ = chat
    outsider = make_user("outsider")

    response = client.post(
        f"/private_chat/{private_chat.id}/message",
        json={"text": "hello"},
        headers=auth_headers(outsider),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not a chat participant"


def test_get_message_success(client, chat, db_session, auth_headers):
    private_chat, user_one, _ = chat
    message = Message.create_message(
        db_session,
        private_chat.id,
        type("Data", (), {"user_id": user_one.uid, "text": "hello"})(),
    )

    response = client.get(
        f"/private_chat/{private_chat.id}/{message.id}",
        headers=auth_headers(user_one),
    )

    assert response.status_code == 200


def test_get_message_not_found(client, chat, auth_headers):
    private_chat, user_one, _ = chat

    response = client.get(
        f"/private_chat/{private_chat.id}/9999",
        headers=auth_headers(user_one),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"


def test_delete_message_success(client, chat, db_session, auth_headers):
    private_chat, user_one, _ = chat
    message = Message.create_message(
        db_session,
        private_chat.id,
        type("Data", (), {"user_id": user_one.uid, "text": "hello"})(),
    )

    response = client.delete(
        f"/private_chat/{private_chat.id}/{message.id}",
        headers=auth_headers(user_one),
    )

    assert response.status_code == 200
    assert response.json() == {"status": "Message deleted"}


def test_delete_message_not_found(client, chat, auth_headers):
    private_chat, user_one, _ = chat

    response = client.delete(
        f"/private_chat/{private_chat.id}/9999",
        headers=auth_headers(user_one),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"
