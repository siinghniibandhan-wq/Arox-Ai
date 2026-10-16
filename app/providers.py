"""Small HTTP clients for cloud AI providers; credentials stay server-side."""

from __future__ import annotations

import os
from typing import Literal

import httpx

Provider = Literal["claude", "openai"]


class ProviderConfigurationError(RuntimeError):
    """Raised when the selected provider is not configured."""


class ProviderRequestError(RuntimeError):
    """Raised when an upstream model request fails."""


async def generate_reply(provider: Provider, prompt: str) -> str:
    timeout = httpx.Timeout(45.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if provider == "claude":
                api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
                if not api_key:
                    raise ProviderConfigurationError("Claude is not configured. Set ANTHROPIC_API_KEY.")
                model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": 1200,
                        "system": "You are AROX, a careful AI development assistant. Prefer lean, clean, maintainable code. Do not claim to have edited repositories or run tests unless tools actually did so. Never ask users to paste secrets into chat.",
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
                data = response.json()
                text_parts = [item.get("text", "") for item in data.get("content", []) if item.get("type") == "text"]
                reply = "\n".join(part for part in text_parts if part).strip()
            else:
                api_key = os.getenv("OPENAI_API_KEY", "").strip()
                if not api_key:
                    raise ProviderConfigurationError("OpenAI is not configured. Set OPENAI_API_KEY.")
                model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "content-type": "application/json"},
                    json={
                        "model": model,
                        "max_tokens": 1200,
                        "messages": [
                            {"role": "system", "content": "You are AROX, a careful AI development assistant. Prefer lean, clean, maintainable code. Do not claim to have edited repositories or run tests unless tools actually did so. Never ask users to paste secrets into chat."},
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                response.raise_for_status()
                data = response.json()
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        except ProviderConfigurationError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
            # Keep upstream response bodies and credentials out of public errors/logs.
            raise ProviderRequestError("The selected AI provider request failed.") from exc

    if not reply:
        raise ProviderRequestError("The selected AI provider returned an empty response.")
    return reply
