def test_search_users_by_name_and_email(client, make_user):
    make_user("Иван Петров", email="ivan@yandex.ru")
    make_user("Мария", email="maria@vk.com")

    by_name = client.get("/users/search", params={"q": "Иван"})
    assert by_name.status_code == 200
    assert len(by_name.json()["users"]) == 1
    assert by_name.json()["users"][0]["username"] == "Иван Петров"

    by_email = client.get("/users/search", params={"q": "maria@"})
    assert by_email.status_code == 200
    assert len(by_email.json()["users"]) == 1
    assert by_email.json()["users"][0]["email"] == "maria@vk.com"


def test_dev_login_and_me(client):
    response = client.post(
        "/auth/dev",
        json={
            "provider": "yandex",
            "email": "demo@yandex.ru",
            "username": "Демо",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["user"]["email"] == "demo@yandex.ru"

    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["user"]["username"] == "Демо"


def test_list_user_chats(client, chat):
    private_chat, user_one, user_two = chat
    response = client.get(f"/users/{user_one.uid}/chats")
    assert response.status_code == 200
    chats = response.json()["chats"]
    assert len(chats) == 1
    assert chats[0]["id"] == private_chat.id
    assert chats[0]["peer"]["uid"] == user_two.uid
