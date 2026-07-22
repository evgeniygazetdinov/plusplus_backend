def test_health_check(client):
    response = client.get("/healf_check")

    assert response.status_code == 200
    assert response.json() == {"message": "alive"}
