import os
from typing import Optional
import asyncpg
from fastapi import FastAPI, HTTPException
import httpx
from pydantic import BaseModel

app = FastAPI(title="AI Workforce Dual Orchestrator", version="2.0.0")

DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "cloud")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "localpassword")
DB_NAME = os.getenv("DB_NAME", "app_db")
DB_SSLMODE = os.getenv("DB_SSLMODE", "prefer")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434/v1")
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:7b")

CLOUD_GATEWAY_URL = os.getenv("CLOUD_GATEWAY_URL", "https://api.groq.com/openai/v1")
CLOUD_API_KEY = os.getenv("CLOUD_API_KEY", "")
CLOUD_MODEL_NAME = os.getenv("CLOUD_MODEL_NAME", "llama-3.3-70b-versatile")


async def get_db_pool():
    ssl_setting = True if DB_SSLMODE == "require" else None
    return await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        ssl=ssl_setting,
        min_size=1,
        max_size=5,
    )


class TaskDispatch(BaseModel):
    requester: str = "Owner"
    instruction: str
    force_local_ram: Optional[bool] = None


@app.get("/")
def get_status():
    return {
        "status": "online",
        "environment": DEPLOYMENT_ENV,
        "compute_engine": (
            "Host Physical RAM (Ollama)"
            if DEPLOYMENT_ENV == "local_hardware"
            else "Cloud Providers"
        ),
        "state_connected_db": f"{DB_HOST}:{DB_PORT}/{DB_NAME}",
    }


@app.post("/ai/dispatch")
async def dispatch_task(task: TaskDispatch):
    use_local_compute = (
        DEPLOYMENT_ENV == "local_hardware" or task.force_local_ram is True
    )

    prompt = f"""System: You are the Chief of Staff agent.
Classify this task into its department (CTO, COO, CFO, HR, Legal, Personal).
Categorize Risk Level:
- Level 0 (Read queries) -> Auto-approved
- Level 1 (Internal drafts) -> Auto-approved & Logged
- Level 2 (External writes, customer dispatch) -> Queued for Owner Approval
- Level 3 (Payments, schema change, production deploy) -> Mandatory Human Approval

Instruction: "{task.instruction}"
Provide a clear, structured JSON-ready plan."""

    executed_by = "local_ram"
    analysis_text = ""

    if use_local_compute:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(
                    f"{OLLAMA_BASE_URL}/chat/completions",
                    json={
                        "model": LOCAL_MODEL_NAME,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                    },
                )
                if res.status_code == 200:
                    analysis_text = res.json()["choices"][0]["message"]["content"]
                    executed_by = f"local_ram ({LOCAL_MODEL_NAME})"
                else:
                    err_msg = f"Local Ollama error code: {res.status_code}"
                    raise RuntimeError(err_msg)
        except Exception as e:
            if CLOUD_API_KEY:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    res = await client.post(
                        f"{CLOUD_GATEWAY_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {CLOUD_API_KEY}"},
                        json={
                            "model": CLOUD_MODEL_NAME,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.2,
                        },
                    )
                    analysis_text = res.json()["choices"][0]["message"]["content"]
                    executed_by = f"cloud_fallback_token ({CLOUD_MODEL_NAME})"
            else:
                raise HTTPException(
                    status_code=500, detail=f"Local execution failed: {e!s}"
                ) from e
    else:
        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(
                f"{CLOUD_GATEWAY_URL}/chat/completions",
                headers={"Authorization": f"Bearer {CLOUD_API_KEY}"},
                json={
                    "model": CLOUD_MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
            )
            analysis_text = res.json()["choices"][0]["message"]["content"]
            executed_by = f"cloud_api ({CLOUD_MODEL_NAME})"

    # Write state directly to central PostgreSQL database
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ai.audit_log (actor, action, target, before, after)
                VALUES ($1, $2, $3, $4, $5)
                """,
                f"Chief_of_Staff [{executed_by}]",
                "task_analyzed",
                "orchestrator",
                None,
                {"requester": task.requester, "plan": analysis_text},
            )
        await pool.close()
    except Exception as db_err:
        print(f"Warning: Could not write central audit log: {db_err}")

    return {
        "status": "success",
        "engine_used": executed_by,
        "hardware_location": (
            "Host Physical RAM"
            if "local_ram" in executed_by
            else "Cloud Provider"
        ),
        "chief_of_staff_plan": analysis_text,
    }
