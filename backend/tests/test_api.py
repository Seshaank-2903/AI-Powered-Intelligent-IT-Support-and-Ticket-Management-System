def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_login_success(client, setup_test_data):
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@test.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure(client, setup_test_data):
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Incorrect email or password"
