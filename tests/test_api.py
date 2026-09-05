from fastapi.testclient import TestClient

from green_v2.api.app import app


client = TestClient(app)


def test_health_contract() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "service": "green-v2-api",
        "status": "ok",
        "version": "0.1.0",
    }


def test_ready_contract() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ping_contract() -> None:
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong", "service": "green-v2-api"}

