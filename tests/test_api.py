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


def test_auto_is_the_default_provider(monkeypatch) -> None:
    monkeypatch.setenv("AROX_ACCESS_TOKEN", "test-secret")

    async def fake_generate_reply(provider: str, prompt: str) -> str:
        assert provider == "auto"
        return "Routed by AROX."

    monkeypatch.setattr("app.main.generate_reply", fake_generate_reply)
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer test-secret"},
        json={"message": "Hello"},
    )
    assert response.status_code == 200
    assert response.json() == {"provider": "auto", "reply": "Routed by AROX."}


def test_provider_status_requires_token_and_hides_secrets(monkeypatch) -> None:
    monkeypatch.setenv("AROX_ACCESS_TOKEN", "test-secret")
    monkeypatch.setenv("FREELLMAPI_BASE_URL", "http://freellmapi:3000/v1")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "must-not-be-returned")
    response = client.get(
        "/api/providers",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["routing"] == "free-first"
    assert {"id": "freellmapi", "configured": True} in payload["providers"]
    assert "must-not-be-returned" not in response.text


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
