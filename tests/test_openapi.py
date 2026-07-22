def test_openapi_schema(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Chat Volc API"
    assert "/users/" in schema["paths"]
    assert "/private_chat/" in schema["paths"]
