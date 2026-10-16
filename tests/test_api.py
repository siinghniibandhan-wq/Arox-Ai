from fastapi.testclient import TestClient

from app.main import app
from app.providers import ProviderConfigurationError, ProviderRequestError

client = TestClient(app)


def test_health_is_public() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "arox-api"


def test_chat_rejects_missing_token(monkeypatch) -> None:
    monkeypatch.setenv("AROX_ACCESS_TOKEN", "test-secret")
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 401


def test_chat_rejects_invalid_token(monkeypatch) -> None:
    monkeypatch.setenv("AROX_ACCESS_TOKEN", "test-secret")
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer wrong-secret"},
        json={"message": "Hello"},
    )
    assert response.status_code == 401


def test_chat_is_disabled_until_access_token_is_configured(monkeypatch) -> None:
    monkeypatch.delenv("AROX_ACCESS_TOKEN", raising=False)
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 503


def test_chat_returns_provider_reply(monkeypatch) -> None:
    monkeypatch.setenv("AROX_ACCESS_TOKEN", "test-secret")

    async def fake_generate_reply(provider: str, prompt: str) -> str:
        assert provider == "claude"
        assert prompt == "Hello AROX"
        return "Hello. Ready to help."

    monkeypatch.setattr("app.main.generate_reply", fake_generate_reply)
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer test-secret"},
        json={"message": "  Hello AROX  ", "provider": "claude"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "provider": "claude",
        "reply": "Hello. Ready to help.",
    }


def test_chat_maps_missing_provider_configuration_to_503(monkeypatch) -> None:
    monkeypatch.setenv("AROX_ACCESS_TOKEN", "test-secret")

    async def fake_generate_reply(provider: str, prompt: str) -> str:
        raise ProviderConfigurationError("Claude is not configured.")

    monkeypatch.setattr("app.main.generate_reply", fake_generate_reply)
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer test-secret"},
        json={"message": "Hello"},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Claude is not configured."


def test_chat_hides_upstream_provider_error_details(monkeypatch) -> None:
    monkeypatch.setenv("AROX_ACCESS_TOKEN", "test-secret")

    async def fake_generate_reply(provider: str, prompt: str) -> str:
        raise ProviderRequestError("The selected AI provider request failed.")

    monkeypatch.setattr("app.main.generate_reply", fake_generate_reply)
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer test-secret"},
        json={"message": "Hello"},
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "The selected AI provider request failed."
