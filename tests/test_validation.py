def test_create_chat_invalid_body(client):
    response = client.post("/private_chat/", json={"user_one_uid": "only-one"})

    assert response.status_code == 422


def test_create_message_invalid_body(client, chat):
    private_chat, _, _ = chat

    response = client.post(
        f"/private_chat/{private_chat.id}/message",
        json={"user_id": "uid-without-text"},
    )

    assert response.status_code == 422
