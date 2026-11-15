import os

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

router = APIRouter()

OMNIROUTE_URL = os.getenv(
    "OMNIROUTE_URL", "http://omniroute:20128/v1"
).rstrip("/")
OMNIROUTE_API_KEY = os.getenv("OMNIROUTE_API_KEY", "")

GENERAL_MODELS = {
    "arox-smart",
    "arox-flash",
    "arox-complex",
}

def is_allowed_model(model):
    return isinstance(model, str) and model in GENERAL_MODELS

@router.get("/coding/v1/models")
async def coding_models():
    return {
        "object": "list",
        "data": [
            {"id": model, "object": "model", "owned_by": "arox"}
            for model in sorted(GENERAL_MODELS)
        ],
    }

@router.post("/coding/v1/chat/completions")
async def coding_completions(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON object required")

    if not is_allowed_model(payload.get("model")):
        raise HTTPException(status_code=403, detail="Model not allowed")

    if not isinstance(payload.get("messages"), list):
        raise HTTPException(status_code=400, detail="messages must be a list")

    if not OMNIROUTE_API_KEY:
        raise HTTPException(status_code=503, detail="Model gateway unavailable")

    client = httpx.AsyncClient(timeout=None)
    try:
        req = client.build_request(
            "POST",
            f"{OMNIROUTE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OMNIROUTE_API_KEY}"},
            json=payload,
        )
        upstream = await client.send(req, stream=bool(payload.get("stream")))
    except httpx.HTTPError:
        await client.aclose()
        raise HTTPException(status_code=502, detail="Upstream unavailable")

    headers = {
        name: upstream.headers[name]
        for name in ("content-type", "cache-control")
        if name in upstream.headers
    }

    if payload.get("stream"):
        if upstream.status_code >= 400:
            body = await upstream.aread()
            status = upstream.status_code
            await upstream.aclose()
            await client.aclose()
            return Response(body, status_code=status, headers=headers)

        async def stream_body():
            try:
                async for chunk in upstream.aiter_raw():
                    yield chunk
            finally:
                await upstream.aclose()
                await client.aclose()

        return StreamingResponse(
            stream_body(),
            status_code=upstream.status_code,
            headers=headers,
        )

    body = await upstream.aread()
    status = upstream.status_code
    await upstream.aclose()
    await client.aclose()
    return Response(body, status_code=status, headers=headers)
