from fastapi.testclient import TestClient

from app.main import app
from app.providers import ProviderConfigurationError, ProviderRequestError

client = TestClient(app)


def test_health_is_public() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "kpmc-ai-api"


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
        assert prompt == "Hello KPMC AI"
        return "Hello. Ready to help."

    monkeypatch.setattr("app.main.generate_reply", fake_generate_reply)
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer test-secret"},
        json={"message": "  Hello KPMC AI  ", "provider": "claude"},
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
        return "Routed by KPMC AI."

    monkeypatch.setattr("app.main.generate_reply", fake_generate_reply)
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer test-secret"},
        json={"message": "Hello"},
    )
    assert response.status_code == 200
    assert response.json() == {"provider": "auto", "reply": "Routed by KPMC AI."}


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
    assert payload["scope"] == "chat-only"
    assert {
        "id": "freellmapi",
        "label": "FreeLLMAPI",
        "configured": True,
        "available": True,
        "features": ["chat"],
        "description": "Chat through the FreeLLMAPI gateway and its configured model pool.",
    } in payload["providers"]
    assert "must-not-be-returned" not in response.text


def test_godmode_tab_is_listed_but_not_available_until_configured(monkeypatch) -> None:
    monkeypatch.setenv("AROX_ACCESS_TOKEN", "test-secret")
    monkeypatch.delenv("GODMODE_BASE_URL", raising=False)
    monkeypatch.delenv("GODMODE_API_KEY", raising=False)
    response = client.get(
        "/api/providers",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 200
    godmode = next(item for item in response.json()["providers"] if item["id"] == "godmode")
    assert godmode["configured"] is False
    assert godmode["available"] is False
    assert godmode["features"] == ["chat"]


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


def test_chat_accepts_godmode_provider(monkeypatch) -> None:
    monkeypatch.setenv("AROX_ACCESS_TOKEN", "test-secret")

    async def fake_generate_reply(provider: str, prompt: str) -> str:
        assert provider == "godmode"
        return "GodMode-compatible chat response."

    monkeypatch.setattr("app.main.generate_reply", fake_generate_reply)
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer test-secret"},
        json={"message": "Hello", "provider": "godmode"},
    )
    assert response.status_code == 200
    assert response.json()["provider"] == "godmode"
