def test_last_five_users_empty(client):
    response = client.get("/users/last_five_users")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "users": []}


def test_last_five_users_returns_users(client, make_user):
    make_user("user1")
    make_user("user2")

    response = client.get("/users/last_five_users")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["users"]) == 2


def test_create_user(client):
    response = client.post("/users/", params={"username": "alice"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "User created"


def test_create_user_without_username(client):
    response = client.post("/users/")

    assert response.status_code == 200
    assert response.json()["status"] == "User created"


def test_delete_user_success(client, make_user):
    user = make_user("to_delete")

    response = client.delete(f"/users/{user.id}")

    assert response.status_code == 200
    assert response.json() == {"status": "User deleted"}


def test_delete_user_not_found(client):
    response = client.delete("/users/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_not_found(client):
    response = client.get("/users/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_success(client, make_user):
    user = make_user("found")

    response = client.get(f"/users/{user.id}")

    assert response.status_code == 200
