"""AROX FastAPI entry point."""

from __future__ import annotations

import hmac
import os
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.providers import ProviderConfigurationError, ProviderRequestError, generate_reply

Provider = Literal["auto", "freellmapi", "omniroute", "godmode", "claude", "openai"]

app = FastAPI(
    title="KPMC AI API",
    description="Authenticated chat API for separately configured AI provider tabs.",
    version="0.3.0",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    provider: Provider = "auto"


class ChatResponse(BaseModel):
    provider: Provider
    reply: str


def require_access_token(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("AROX_ACCESS_TOKEN", "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="KPMC AI API is not configured. Set AROX_ACCESS_TOKEN in the service environment.",
        )
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Valid bearer token required.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "kpmc-ai-api", "version": "0.3.0"}


@app.get("/api/providers", dependencies=[Depends(require_access_token)])
def providers() -> dict[str, object]:
    """Describe chat tabs and their configured state without exposing credentials."""
    configured = {
        "freellmapi": bool(os.getenv("FREELLMAPI_BASE_URL", "").strip()),
        "omniroute": bool(os.getenv("OMNIROUTE_BASE_URL", "").strip()),
        "godmode": bool(
            os.getenv("GODMODE_BASE_URL", "").strip()
            and os.getenv("GODMODE_API_KEY", "").strip()
        ),
        "claude": bool(os.getenv("ANTHROPIC_API_KEY", "").strip()),
        "openai": bool(os.getenv("OPENAI_API_KEY", "").strip()),
    }
    labels = {
        "freellmapi": "FreeLLMAPI",
        "omniroute": "OmniRoute",
        "godmode": "GodMode",
        "claude": "Claude",
        "openai": "OpenAI",
    }
    descriptions = {
        "freellmapi": "Chat through the FreeLLMAPI gateway and its configured model pool.",
        "omniroute": "Chat through the configured OmniRoute-compatible endpoint.",
        "godmode": "Chat through a separately configured GodMode-compatible endpoint; configure only after its API contract is verified.",
        "claude": "Direct Claude chat API.",
        "openai": "Direct OpenAI chat API.",
    }
    return {
        "default": "auto",
        "routing": "free-first",
        "scope": "chat-only",
        "providers": [
            {
                "id": name,
                "label": labels[name],
                "configured": is_configured,
                "available": is_configured,
                "features": ["chat"],
                "description": descriptions[name],
            }
            for name, is_configured in configured.items()
        ],
    }


@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(require_access_token)])
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        reply = await generate_reply(request.provider, request.message.strip())
    except ProviderConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(provider=request.provider, reply=reply)
