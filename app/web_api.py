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


# ---- Agents: write endpoints (session protected) ----
from pydantic import BaseModel, Field  # noqa: E402

from app.skills_agents import AgentIn, RunIn, SCOPES, create_agent, run_agent  # noqa: E402


class AgentEditIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    job: str | None = Field(default=None, min_length=1, max_length=4000)
    skills: list[str] | None = None
    memory_scope: str | None = None
    is_active: bool | None = None


@router.post("/web/agents")
async def web_agent_create(a: AgentIn, request: Request,
                           x_session: str = Header(default="")):
    from app.main import audit
    await need_session(x_session)
    r = await create_agent(a, request)
    await audit("Owner (web)", "agent_create", r["id"], None,
                {"name": a.name, "skills": a.skills,
                 "memory_scope": a.memory_scope})
    return r


@router.post("/web/agents/{agent_id}")
async def web_agent_edit(agent_id: str, e: AgentEditIn, request: Request,
                         x_session: str = Header(default="")):
    from app.main import audit
    await need_session(x_session)
    try:
        uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="No such agent")
    if e.memory_scope is not None and e.memory_scope not in SCOPES:
        raise HTTPException(status_code=400, detail="Bad memory_scope")
    async with request.app.state.pool.acquire() as c:
        old = await c.fetchrow(
            "SELECT name, system_prompt, skills, memory_scope, is_active"
            " FROM ai.agents WHERE id = $1::uuid", agent_id)
        if not old:
            raise HTTPException(status_code=404, detail="No such agent")
        skills = e.skills if e.skills is not None else json.loads(old["skills"])
        if e.skills is not None:
            known = await c.fetch(
                "SELECT name FROM ai.skills WHERE name = ANY($1::text[])", skills)
            missing = set(skills) - {r["name"] for r in known}
            if missing:
                raise HTTPException(
                    status_code=400, detail=f"Unknown skills: {sorted(missing)}")
        new = {
            "name": e.name if e.name is not None else old["name"],
            "job": e.job if e.job is not None else old["system_prompt"],
            "skills": skills,
            "memory_scope": (e.memory_scope if e.memory_scope is not None
                             else old["memory_scope"]),
            "is_active": (e.is_active if e.is_active is not None
                          else old["is_active"]),
        }
        await c.execute(
            "UPDATE ai.agents SET name=$2, system_prompt=$3, skills=$4::jsonb,"
            " memory_scope=$5, is_active=$6 WHERE id=$1::uuid",
            agent_id, new["name"], new["job"], json.dumps(skills),
            new["memory_scope"], new["is_active"])
    await audit("Owner (web)", "agent_edit", agent_id,
                {"name": old["name"], "job": old["system_prompt"][:300],
                 "skills": json.loads(old["skills"]),
                 "memory_scope": old["memory_scope"],
                 "is_active": old["is_active"]},
                {"name": new["name"], "job": new["job"][:300],
                 "skills": skills, "memory_scope": new["memory_scope"],
                 "is_active": new["is_active"]})
    return {"id": agent_id, "name": new["name"]}


@router.post("/web/agents/{agent_id}/run")
async def web_agent_run(agent_id: str, body: RunIn, request: Request,
                        x_session: str = Header(default="")):
    await need_session(x_session)
    body.requester = "Owner (web)"
    return await run_agent(agent_id, body, request)


# ---- Chief of Staff delegation (session protected) ----
DELEGATE_KEYS = [
    ("CTO Agent", ["code", "bug", "github", "deploy", "server", "debug", "software", "website", "api", "database", "docker", "security", "repository", "test"]),
    ("CFO Agent", ["gst", "tax", "invoice", "budget", "account", "financ", "reconcil", "payment", "invest", "debt", "loan", "bank", "insurance", "valuation", "profit", "cash flow", "equity", "mutual fund", "portfolio", "interest rate", "audit", "treasury"]),
    ("CMO Agent", ["marketing", "brand", "campaign", "advert", "social media", "content", "seo", "promotion"]),
    ("CSO Agent", ["sales", "lead", "customer acquisition", "revenue", "prospect", "negotiat", "pipeline", "quote", "deal"]),
    ("CHRO Agent", ["hire", "hiring", "recruit", "payroll", "employee", "salary", "interview", "attendance", "training", "performance review"]),
    ("CLO Agent", ["legal", "contract", "compliance", "licen", "lawyer", "trademark", "copyright", "lawsuit", "privacy", "court"]),
    ("COO Agent", ["operation", "vendor", "process", "supplier", "logistics", "inventory", "stock", "warehouse", "shipping", "quality", "project"]),
    ("CCO Agent", ["support", "complaint", "refund", "customer service", "ticket", "voice", "phone", "helpdesk", "return"]),
]


@router.post("/web/delegate")
async def web_delegate(body: RunIn, request: Request,
                       x_session: str = Header(default="")):
    from fastapi import HTTPException
    await need_session(x_session)
    text = body.instruction.lower()
    best, best_hits = "Chief of Staff Core", 0
    for name, words in DELEGATE_KEYS:
        hits = sum(1 for w in words if w in text)
        if hits > best_hits:
            best, best_hits = name, hits
    async with request.app.state.pool.acquire() as c:
        aid = await c.fetchval(
            "SELECT id::text FROM ai.agents WHERE name = $1 AND is_active", best)
    if not aid:
        raise HTTPException(status_code=404, detail="Executive not active")
    body.requester = "Owner (web, via Chief of Staff)"
    out = await run_agent(aid, body, request)
    out["delegated_to"] = best
    return out
