from chat_volc.models.models import Message


def test_create_message_success(client, chat):
    private_chat, user_one, _ = chat

    response = client.post(
        f"/private_chat/{private_chat.id}/message",
        json={"user_id": user_one.uid, "text": "hello"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Message created"
    assert data["new_message"]["text"] == "hello"
    assert "id" in data["new_message"]


def test_create_message_chat_not_found(client, make_user):
    user = make_user("orphan")

    response = client.post(
        "/private_chat/9999/message",
        json={"user_id": user.uid, "text": "hello"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "chat or user not found"


def test_create_message_user_not_found(client, chat):
    private_chat, _, _ = chat

    response = client.post(
        f"/private_chat/{private_chat.id}/message",
        json={"user_id": "unknown-uid", "text": "hello"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "chat or user not found"


def test_create_message_user_not_in_chat(client, chat, make_user):
    private_chat, _, _ = chat
    outsider = make_user("outsider")

    response = client.post(
        f"/private_chat/{private_chat.id}/message",
        json={"user_id": outsider.uid, "text": "hello"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "chat or user not found"


def test_get_message_success(client, chat, db_session):
    private_chat, user_one, _ = chat
    message = Message.create_message(
        db_session,
        private_chat.id,
        type("Data", (), {"user_id": user_one.uid, "text": "hello"})(),
    )

    response = client.get(f"/private_chat/{private_chat.id}/{message.id}")

    assert response.status_code == 200


def test_get_message_not_found(client, chat):
    private_chat, _, _ = chat

    response = client.get(f"/private_chat/{private_chat.id}/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"


def test_delete_message_success(client, chat, db_session):
    private_chat, user_one, _ = chat
    message = Message.create_message(
        db_session,
        private_chat.id,
        type("Data", (), {"user_id": user_one.uid, "text": "hello"})(),
    )

    response = client.delete(f"/private_chat/{private_chat.id}/{message.id}")

    assert response.status_code == 200
    assert response.json() == {"status": "Message deleted"}


def test_delete_message_not_found(client, chat):
    private_chat, _, _ = chat

    response = client.delete(f"/private_chat/{private_chat.id}/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"
