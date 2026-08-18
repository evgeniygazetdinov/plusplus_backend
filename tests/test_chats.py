from chat_volc.models.models import Message


def test_create_chat_success(client, two_users, auth_headers):
    user_one, user_two = two_users

    response = client.post(
        "/private_chat/",
        json={"user_one_uid": user_one.uid, "user_two_uid": user_two.uid},
        headers=auth_headers(user_one),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "private Chat created"
    assert "id" in data["new_chat"]


def test_create_chat_requires_auth(client, two_users):
    user_one, user_two = two_users

    response = client.post(
        "/private_chat/",
        json={"user_one_uid": user_one.uid, "user_two_uid": user_two.uid},
    )

    assert response.status_code == 401


def test_create_chat_user_not_found(client, make_user, auth_headers):
    user = make_user("lonely")

    response = client.post(
        "/private_chat/",
        json={"user_one_uid": user.uid, "user_two_uid": "non-existent-uid"},
        headers=auth_headers(user),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "one of users not found"


def test_create_chat_duplicate_returns_409(client, two_users, auth_headers):
    user_one, user_two = two_users
    payload = {"user_one_uid": user_one.uid, "user_two_uid": user_two.uid}
    headers = auth_headers(user_one)

    first = client.post("/private_chat/", json=payload, headers=headers)
    second = client.post("/private_chat/", json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"]["message"] == (
        "Chat already exists between these two users."
    )
    assert second.json()["detail"]["chat_id"] == first.json()["new_chat"]["id"]


def test_create_chat_duplicate_reverse_order_returns_409(client, chat, two_users, auth_headers):
    user_one, user_two = two_users

    response = client.post(
        "/private_chat/",
        json={"user_one_uid": user_two.uid, "user_two_uid": user_one.uid},
        headers=auth_headers(user_two),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["chat_id"] == chat[0].id


def test_get_chat_success(client, chat, auth_headers):
    private_chat, user_one, _ = chat

    response = client.get(
        f"/private_chat/{private_chat.id}",
        headers=auth_headers(user_one),
    )

    assert response.status_code == 200


def test_get_chat_forbidden_for_outsider(client, chat, make_user, auth_headers):
    private_chat, _, _ = chat
    outsider = make_user("outsider")

    response = client.get(
        f"/private_chat/{private_chat.id}",
        headers=auth_headers(outsider),
    )

    assert response.status_code == 403


def test_get_chat_not_found(client, make_user, auth_headers):
    user = make_user("solo")
    response = client.get("/private_chat/9999", headers=auth_headers(user))

    assert response.status_code == 404
    assert response.json()["detail"] == "private_chat not found"


def test_get_all_messages_empty(client, chat, auth_headers):
    private_chat, user_one, _ = chat

    response = client.get(
        f"/private_chat/{private_chat.id}/all_messages",
        headers=auth_headers(user_one),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_all_messages_with_messages(client, chat, db_session, auth_headers):
    private_chat, user_one, _ = chat
    message = Message.create_message(
        db_session,
        private_chat.id,
        type("Data", (), {"user_id": user_one.uid, "text": "hello"})(),
    )

    response = client.get(
        f"/private_chat/{private_chat.id}/all_messages",
        headers=auth_headers(user_one),
    )

    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 1
    assert messages[0]["id"] == message.id


def test_get_all_messages_chat_not_found(client, make_user, auth_headers):
    user = make_user("solo")
    response = client.get(
        "/private_chat/9999/all_messages",
        headers=auth_headers(user),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "private_chat not found"


def test_delete_chat_success(client, chat, auth_headers):
    private_chat, user_one, _ = chat

    response = client.delete(
        f"/private_chat/{private_chat.id}",
        headers=auth_headers(user_one),
    )

    assert response.status_code == 200
    assert response.json() == {"status": "private_chat deleted"}


def test_delete_chat_not_found(client, make_user, auth_headers):
    user = make_user("solo")
    response = client.delete("/private_chat/9999", headers=auth_headers(user))

    assert response.status_code == 404
    assert response.json()["detail"] == "private_chat not found"
