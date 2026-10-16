from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_public() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_rejects_missing_token(monkeypatch) -> None:
    monkeypatch.setenv("AROX_ACCESS_TOKEN", "test-secret")
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 401


def test_chat_is_disabled_until_access_token_is_configured(monkeypatch) -> None:
    monkeypatch.delenv("AROX_ACCESS_TOKEN", raising=False)
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 503
