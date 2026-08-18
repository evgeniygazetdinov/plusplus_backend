def test_last_five_users_empty(client, make_user, auth_headers):
    user = make_user("admin")
    response = client.get("/users/last_five_users", headers=auth_headers(user))

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert len(response.json()["users"]) == 1


def test_last_five_users_returns_users(client, make_user, auth_headers):
    make_user("user1")
    make_user("user2")
    user = make_user("viewer")

    response = client.get("/users/last_five_users", headers=auth_headers(user))

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["users"]) == 3


def test_create_user(client, make_user, auth_headers):
    user = make_user("creator")
    response = client.post(
        "/users/",
        params={"username": "alice"},
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "User created"


def test_create_user_without_username(client, make_user, auth_headers):
    user = make_user("creator")
    response = client.post("/users/", headers=auth_headers(user))

    assert response.status_code == 200
    assert response.json()["status"] == "User created"


def test_delete_user_success(client, make_user, auth_headers):
    user = make_user("to_delete")

    response = client.delete(
        f"/users/{user.uid}",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json() == {"status": "User deleted"}


def test_delete_user_forbidden_for_other_uid(client, make_user, auth_headers):
    user = make_user("actor")
    other = make_user("other")
    response = client.delete(
        f"/users/{other.uid}",
        headers=auth_headers(user),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


def test_get_user_not_found(client, make_user, auth_headers):
    user = make_user("viewer")
    response = client.get("/users/non-existent-uid", headers=auth_headers(user))

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_success(client, make_user, auth_headers):
    user = make_user("found")

    response = client.get(
        f"/users/{user.uid}",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["uid"] == user.uid
