"""AROX FastAPI entry point."""

from __future__ import annotations

import hmac
import os
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.providers import ProviderConfigurationError, ProviderRequestError, generate_reply

ProviderName = Literal["gemini", "claude", "openai"]

app = FastAPI(
    title="AROX AI Development Assistant",
    description="A minimal cloud API for a multi-provider AI coding assistant.",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    provider: ProviderName = "gemini"


class ChatResponse(BaseModel):
    provider: ProviderName
    reply: str


def require_access_token(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("AROX_ACCESS_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="AROX is not configured yet. Set AROX_ACCESS_TOKEN in the service environment.")
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Valid bearer token required.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "arox-api", "version": "0.1.0"}


@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(require_access_token)])
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        reply = await generate_reply(request.provider, request.message.strip())
    except ProviderConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(provider=request.provider, reply=reply)
