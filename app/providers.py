"""Server-side adapters for direct models and OpenAI-compatible AI gateways."""

from __future__ import annotations

import os
from typing import Literal

import httpx

Provider = Literal["auto", "freellmapi", "omniroute", "godmode", "claude", "openai"]


class ProviderConfigurationError(RuntimeError):
    """Raised when the selected provider is not configured."""


class ProviderRequestError(RuntimeError):
    """Raised when an upstream model request fails."""


SYSTEM_PROMPT = (
    "You are KPMC AI, a careful and helpful chat assistant. "
    "Answer the user's request directly. Do not claim to have edited repositories "
    "or run tests unless tools actually did so. Never ask users to paste secrets into chat."
)


def _gateway_url(base_url: str) -> str:
    """Return the OpenAI-compatible chat-completions URL for a gateway base URL."""
    base = base_url.strip().rstrip("/")
    if not base:
        return ""
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


async def _openai_compatible_reply(
    client: httpx.AsyncClient,
    *,
    name: str,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
) -> str:
    url = _gateway_url(base_url)
    if not url:
        raise ProviderConfigurationError(f"{name} is not configured. Set its base URL.")
    headers = {"content-type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    response = await client.post(
        url,
        headers=headers,
        json={
            "model": model,
            "max_tokens": 1200,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        },
    )
    response.raise_for_status()
    data = response.json()
    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not isinstance(reply, str) or not reply.strip():
        raise ProviderRequestError(f"{name} returned an empty response.")
    return reply.strip()


async def _direct_reply(client: httpx.AsyncClient, provider: str, prompt: str) -> str:
    if provider == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise ProviderConfigurationError("Claude is not configured. Set ANTHROPIC_API_KEY.")
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
                "max_tokens": 1200,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()
        text_parts = [
            item.get("text", "")
            for item in data.get("content", [])
            if item.get("type") == "text"
        ]
        reply = "\n".join(part for part in text_parts if part).strip()
    else:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ProviderConfigurationError("OpenAI is not configured. Set OPENAI_API_KEY.")
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "content-type": "application/json"},
            json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                "max_tokens": 1200,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        response.raise_for_status()
        data = response.json()
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

    if not reply:
        raise ProviderRequestError(f"{provider} returned an empty response.")
    return reply


def _gateway_config(provider: str) -> tuple[str, str, str, str]:
    """Return name, base URL, key, and model for a configured gateway."""
    settings = {
        "freellmapi": (
            "FreeLLMAPI", "FREELLMAPI_BASE_URL", "FREELLMAPI_API_KEY", "FREELLMAPI_MODEL"
        ),
        "omniroute": (
            "OmniRoute", "OMNIROUTE_BASE_URL", "OMNIROUTE_API_KEY", "OMNIROUTE_MODEL"
        ),
        "godmode": (
            "GodMode-compatible gateway", "GODMODE_BASE_URL", "GODMODE_API_KEY", "GODMODE_MODEL"
        ),
    }
    name, url_env, key_env, model_env = settings[provider]
    return (
        name,
        os.getenv(url_env, "").strip(),
        os.getenv(key_env, "").strip(),
        os.getenv(model_env, "auto").strip() or "auto",
    )


async def generate_reply(provider: Provider, prompt: str) -> str:
    """Generate chat from a selected provider or use free-first gateway fallback.

    Auto mode attempts configured free-first gateways in order, then direct providers
    only when explicitly configured. GodMode is treated as a separate compatible
    endpoint, not as a claim that the upstream GodMode project itself is an API gateway.
    """
    timeout = httpx.Timeout(45.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if provider == "auto":
            candidates = [
                _gateway_config(name)
                for name in ("freellmapi", "omniroute", "godmode")
                if os.getenv({
                    "freellmapi": "FREELLMAPI_BASE_URL",
                    "omniroute": "OMNIROUTE_BASE_URL",
                    "godmode": "GODMODE_BASE_URL",
                }[name], "").strip()
            ]
            for name, base_url, api_key, model in candidates:
                try:
                    return await _openai_compatible_reply(
                        client, name=name, base_url=base_url, api_key=api_key,
                        model=model, prompt=prompt,
                    )
                except (httpx.HTTPError, ValueError, KeyError, IndexError, ProviderRequestError):
                    continue

            for name in ("claude", "openai"):
                env_key = "ANTHROPIC_API_KEY" if name == "claude" else "OPENAI_API_KEY"
                if not os.getenv(env_key, "").strip():
                    continue
                try:
                    return await _direct_reply(client, name, prompt)
                except (httpx.HTTPError, ValueError, KeyError, IndexError, ProviderRequestError):
                    continue

            if not candidates and not any(
                os.getenv(key, "").strip()
                for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")
            ):
                raise ProviderConfigurationError(
                    "No AI provider is configured. Set FREELLMAPI_BASE_URL, "
                    "OMNIROUTE_BASE_URL, GODMODE_BASE_URL, or a direct provider API key."
                )
            raise ProviderRequestError(
                "All configured AI routes failed. Check gateway health, model availability, and rate limits."
            )

        if provider in ("freellmapi", "omniroute", "godmode"):
            name, base_url, api_key, model = _gateway_config(provider)
            try:
                return await _openai_compatible_reply(
                    client, name=name, base_url=base_url, api_key=api_key,
                    model=model, prompt=prompt,
                )
            except (ProviderConfigurationError, ProviderRequestError):
                raise
            except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
                raise ProviderRequestError("The selected AI provider request failed.") from exc

        try:
            return await _direct_reply(client, provider, prompt)
        except (ProviderConfigurationError, ProviderRequestError):
            raise
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
            raise ProviderRequestError("The selected AI provider request failed.") from exc
