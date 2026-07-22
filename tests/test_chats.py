from chat_volc.models.models import Message


def test_create_chat_success(client, two_users):
    user_one, user_two = two_users

    response = client.post(
        "/private_chat/",
        json={"user_one_uid": user_one.uid, "user_two_uid": user_two.uid},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "private Chat created"
    assert "id" in data["new_chat"]


def test_create_chat_user_not_found(client, make_user):
    user = make_user("lonely")

    response = client.post(
        "/private_chat/",
        json={"user_one_uid": user.uid, "user_two_uid": "non-existent-uid"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "one of users not found"


def test_create_chat_duplicate_returns_409(client, two_users):
    user_one, user_two = two_users
    payload = {"user_one_uid": user_one.uid, "user_two_uid": user_two.uid}

    first = client.post("/private_chat/", json=payload)
    second = client.post("/private_chat/", json=payload)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"]["message"] == (
        "Chat already exists between these two users."
    )
    assert second.json()["detail"]["chat_id"] == first.json()["new_chat"]["id"]


def test_create_chat_duplicate_reverse_order_returns_409(client, chat, two_users):
    user_one, user_two = two_users

    response = client.post(
        "/private_chat/",
        json={"user_one_uid": user_two.uid, "user_two_uid": user_one.uid},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["chat_id"] == chat[0].id


def test_get_chat_success(client, chat):
    private_chat, _, _ = chat

    response = client.get(f"/private_chat/{private_chat.id}")

    assert response.status_code == 200


def test_get_chat_not_found(client):
    response = client.get("/private_chat/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "private_chat not found"


def test_get_all_messages_empty(client, chat):
    private_chat, _, _ = chat

    response = client.get(f"/private_chat/{private_chat.id}/all_messages")

    assert response.status_code == 200
    assert response.json() == []


def test_get_all_messages_with_messages(client, chat, db_session):
    private_chat, user_one, _ = chat
    message = Message.create_message(
        db_session,
        private_chat.id,
        type("Data", (), {"user_id": user_one.uid, "text": "hello"})(),
    )

    response = client.get(f"/private_chat/{private_chat.id}/all_messages")

    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 1
    assert messages[0]["id"] == message.id


def test_get_all_messages_chat_not_found(client):
    response = client.get("/private_chat/9999/all_messages")

    assert response.status_code == 404
    assert response.json()["detail"] == "private_chat not found"


def test_delete_chat_success(client, chat):
    private_chat, _, _ = chat

    response = client.delete(f"/private_chat/{private_chat.id}")

    assert response.status_code == 200
    assert response.json() == {"status": "private_chat deleted"}


def test_delete_chat_not_found(client):
    response = client.delete("/private_chat/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "private_chat not found"
