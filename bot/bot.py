import os, asyncio, logging
import httpx

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OWNER = int(os.environ["OWNER_TELEGRAM_ID"])
KEY = os.environ["APPROVER_KEY"]
API = "http://orchestrator:8000"
TG = f"https://api.telegram.org/bot{TOKEN}"
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("arox-bot")
seen = set()


async def tg(c, method, **data):
    r = await c.post(f"{TG}/{method}", json=data, timeout=40)
    return r.json()


async def api(c, verb, path, **params):
    r = await c.request(verb, API + path, params=params,
                        headers={"X-API-Key": KEY}, timeout=30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {}


def buttons(aid, level):
    first = "Approve" if level < 3 else "Approve (L3)"
    return {"inline_keyboard": [[
        {"text": first, "callback_data": f"a:{aid}"},
        {"text": "Reject", "callback_data": f"r:{aid}"},
    ]]}

logging.getLogger("httpx").setLevel(logging.WARNING)


async def show_pending(c):
    code, rows = await api(c, "GET", "/approvals", status="pending")
    if code != 200 or not isinstance(rows, list):
        await tg(c, "sendMessage", chat_id=OWNER, text=f"List failed ({code})")
        return
    if not rows:
        await tg(c, "sendMessage", chat_id=OWNER, text="No pending approvals.")
    for r in rows:
        text = (f"#{r['id']} Level {r['level']}: {r['tool']}\n"
                f"From: {r['requester']}\nArgs: {str(r['args'])[:500]}")
        await tg(c, "sendMessage", chat_id=OWNER, text=text,
                 reply_markup=buttons(r["id"], r["level"]))


async def on_callback(c, cq):
    if cq["from"]["id"] != OWNER:
        return
    act, _, aid = cq.get("data", "").partition(":")
    if not aid.isdigit():
        return
    if act == "r":
        code, out = await api(c, "POST", f"/approvals/{aid}/reject")
        msg = "Rejected" if code == 200 else f"Reject failed ({code})"
    elif act in ("a", "c"):
        extra = {"confirm": "yes"} if act == "c" else {}
        code, out = await api(c, "POST", f"/approvals/{aid}/approve", **extra)
        if code == 400 and act == "a":
            ask = {"inline_keyboard": [[{"text": "Yes, confirm",
                                         "callback_data": f"c:{aid}"}]]}
            await tg(c, "sendMessage", chat_id=OWNER, reply_markup=ask,
                     text=f"Level 3 action #{aid}. Tap to confirm.")
            msg = "Needs confirmation"
        elif code == 200:
            msg = f"Approved: {out.get('status')}"
        else:
            msg = f"Approve failed ({code})"
    else:
        return
    await tg(c, "answerCallbackQuery", callback_query_id=cq["id"], text=msg)
    await tg(c, "sendMessage", chat_id=OWNER, text=f"#{aid}: {msg}")


async def main():
    async with httpx.AsyncClient() as c:
        await tg(c, "deleteWebhook", drop_pending_updates=True)
        log.info("bot started")
        offset = 0
        while True:
            try:
                res = await tg(c, "getUpdates", offset=offset, timeout=30)
                for u in res.get("result", []):
                    offset = u["update_id"] + 1
                    if "callback_query" in u:
                        await on_callback(c, u["callback_query"])
                    elif "message" in u:
                        m = u["message"]
                        if m.get("from", {}).get("id") != OWNER:
                            continue
                        if m.get("text", "").startswith(("/pending", "/start")):
                            await show_pending(c)
            except Exception as e:
                log.warning("loop error: %s", type(e).__name__)
                await asyncio.sleep(5)


asyncio.run(main())
