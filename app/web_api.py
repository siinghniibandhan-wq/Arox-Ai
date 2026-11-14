import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request

from app.chat import CHAT_DAILY_LIMIT, need_session, rds

router = APIRouter()


@router.get("/web/pending")
async def web_pending(request: Request, all: int = 0,
                      x_session: str = Header(default="")):
    await need_session(x_session)
    where = "" if all else "WHERE decided_at IS NULL "
    async with request.app.state.pool.acquire() as c:
        rows = await c.fetch(
            "SELECT id, created_at, decided_at, requester, tool, level,"
            " status, left(args::text, 300) AS args"
            " FROM ai.pending_actions " + where +
            "ORDER BY created_at DESC LIMIT 50")
    return [dict(r) for r in rows]


@router.get("/web/activity")
async def web_activity(request: Request,
                       x_session: str = Header(default="")):
    await need_session(x_session)
    async with request.app.state.pool.acquire() as c:
        rows = await c.fetch(
            "SELECT id, actor, action, target, created_at,"
            " left(after::text, 120) AS after"
            " FROM ai.audit_log ORDER BY created_at DESC LIMIT 50")
    return [dict(r) for r in rows]


@router.get("/web/skills")
async def web_skills(request: Request,
                     x_session: str = Header(default="")):
    await need_session(x_session)
    async with request.app.state.pool.acquire() as c:
        rows = await c.fetch(
            "SELECT name, description, version FROM ai.skills ORDER BY name")
    return [dict(r) for r in rows]


@router.get("/web/agents")
async def web_agents(request: Request,
                     x_session: str = Header(default="")):
    await need_session(x_session)
    async with request.app.state.pool.acquire() as c:
        rows = await c.fetch(
            "SELECT id, name, system_prompt, skills, memory_scope, is_active"
            " FROM ai.agents ORDER BY created_at DESC LIMIT 100")
    return [
        {"id": str(r["id"]), "name": r["name"], "job": r["system_prompt"],
         "skills": json.loads(r["skills"]),
         "memory_scope": r["memory_scope"], "is_active": r["is_active"]}
        for r in rows
    ]


@router.get("/web/status")
async def web_status(request: Request,
                     x_session: str = Header(default="")):
    await need_session(x_session)
    out = {}
    async with request.app.state.pool.acquire() as c:
        out["database"] = "ok"
        out["pending"] = await c.fetchval(
            "SELECT count(*) FROM ai.pending_actions"
            " WHERE decided_at IS NULL")
        out["skills"] = await c.fetchval("SELECT count(*) FROM ai.skills")
        out["agents"] = await c.fetchval(
            "SELECT count(*) FROM ai.agents WHERE is_active")
    try:
        r = rds()
        await r.ping()
        out["redis"] = "ok"
        today = datetime.now(timezone.utc).date().isoformat()
        out["chat_used_today"] = int(await r.get(f"chat:daily:{today}") or 0)
    except Exception:
        out["redis"] = "error"
    out["chat_daily_limit"] = CHAT_DAILY_LIMIT
    return out


@router.get("/web/chats")
async def web_chats(request: Request, x_session: str = Header(default="")):
    await need_session(x_session)
    async with request.app.state.pool.acquire() as c:
        rows = await c.fetch(
            "SELECT id, title, updated_at FROM ai.chat_sessions"
            " ORDER BY updated_at DESC LIMIT 50")
    return [{"id": str(r["id"]), "title": r["title"],
             "updated_at": r["updated_at"]} for r in rows]


@router.get("/web/chats/{chat_id}")
async def web_chat_one(chat_id: str, request: Request,
                       x_session: str = Header(default="")):
    await need_session(x_session)
    try:
        sid = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
    async with request.app.state.pool.acquire() as c:
        rows = await c.fetch(
            "SELECT role, text, engine, created_at FROM ai.chat_messages"
            " WHERE session_id = $1 ORDER BY id LIMIT 500", sid)
    return [dict(r) for r in rows]
