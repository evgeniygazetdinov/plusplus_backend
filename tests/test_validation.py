def test_create_chat_invalid_body(client, make_user, auth_headers):
    user = make_user("actor")
    response = client.post(
        "/private_chat/",
        json={"user_one_uid": "only-one"},
        headers=auth_headers(user),
    )

    assert response.status_code == 422


def test_create_message_invalid_body(client, chat, auth_headers):
    private_chat, user_one, _ = chat

    response = client.post(
        f"/private_chat/{private_chat.id}/message",
        json={},
        headers=auth_headers(user_one),
    )

    assert response.status_code == 422
