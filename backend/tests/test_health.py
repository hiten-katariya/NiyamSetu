from unittest.mock import patch
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["status"] == "healthy"
    assert "version" in data["data"]
    assert "environment" in data["data"]


def test_readiness_check_success(client: TestClient):
    with patch("backend.app.services.health_service.check_db_connection", return_value=(True, "Database connected")):
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "ready"
        assert data["data"]["database"]["status"] == "connected"


def test_readiness_check_failure(client: TestClient):
    with patch("backend.app.services.health_service.check_db_connection", return_value=(False, "Connection refused")):
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["data"]["status"] == "not_ready"
        assert data["data"]["database"]["status"] == "disconnected"


def test_validation_error_format(client: TestClient):
    # Post invalid payload to auth login (empty password / invalid email)
    response = client.post("/api/v1/auth/login", json={"email": "not-an-email", "password": "123"})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(data["error"]["details"], list)
    assert len(data["error"]["details"]) > 0
