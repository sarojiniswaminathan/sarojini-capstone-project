import asyncio
import json
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from agent.db import get_connection
from agent import agent as agent_mod
from agent import email_intake, google_calendar, inventory, planning
from calendar_api import router as calendar_router
from email_api import router as email_router
from inventory_api import router as inventory_router

logger = logging.getLogger("tailoring_agent.email_poll")

app = FastAPI(title="Tailoring Business Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(calendar_router)
app.include_router(inventory_router)
app.include_router(email_router)


async def _email_poll_loop():
    """Runs for the lifetime of the server: periodically checks the inbox
    for new orders/replies/supplier updates (agent/email_intake.py) and
    checks whether any pending order's confirmation invite has been
    answered yet. A single bad cycle (Google/AI hiccup, one bad email) must
    never kill the loop — it just logs and tries again next interval."""
    interval = int(os.environ.get("EMAIL_POLL_INTERVAL_SECONDS", "180"))
    while True:
        try:
            conn = get_connection()
            email_intake.poll_and_process(conn)
            email_intake.check_pending_confirmations(conn)
        except Exception:
            logger.exception("Email poll cycle failed")
        await asyncio.sleep(interval)


@app.on_event("startup")
async def _start_email_poller():
    asyncio.create_task(_email_poll_loop())


class ChatRequest(BaseModel):
    message: str


def _stringify_direct_result(result):
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        if "message" in result:
            return result["message"]
        if "all_materials_available" in result:
            order_id = result.get("order_id", "this order")
            ready = result.get("all_materials_available")
            if ready:
                return f"All required materials for {order_id} are available."
            shortages = []
            for item in result.get("materials", []):
                if item.get("shortage", 0) > 0:
                    shortages.append(f"{item['material']} ({item['shortage']} {item['unit']})")
            if shortages:
                return f"{order_id} is short on: {', '.join(shortages)}."
            return f"I couldn't confirm material readiness for {order_id}."
        if "recommended_order_id" in result:
            return (
                f"Recommended order: {result['recommended_order_id']} for {result.get('customer', 'customer')} "
                f"({result.get('garment', 'garment')}). Score: {result.get('score')}"
            )
        if "available_qty" in result:
            return (
                f"{result.get('name', 'Material')} has {result.get('available_qty', 0)} {result.get('unit', '')} "
                f"available, with {result.get('physical_qty', 0)} total and {result.get('reserved_qty', 0)} reserved."
            )
        return json.dumps(result, default=str)
    if isinstance(result, list):
        return json.dumps(result, default=str)
    return str(result)


def _find_material_match(conn, message):
    lowered = re.sub(r"[^a-z0-9\s-]", " ", message.lower())
    rows = inventory.list_materials(conn)
    best_match = None
    best_score = -1

    for row in rows:
        name = (row["name"] or "").lower()
        color = (row["color"] or "").lower()
        material_id = (row["id"] or "").lower()
        score = 0
        if name and name in lowered:
            score += 5
        if color and color in lowered:
            score += 3
        if material_id and material_id in lowered:
            score += 4
        if score > best_score:
            best_score = score
            best_match = row

    if best_score > 0:
        return best_match
    return None


def _inventory_rows_for_request(conn, message):
    """Return only the inventory rows named or implied by the request."""
    q = message.lower()
    category = None
    name_contains = None
    color = None

    category_terms = {
        "fabric": "fabric",
        "fabrics": "fabric",
        "cloth": "fabric",
        "textile": "fabric",
        "textiles": "fabric",
        "zipper": "fastening",
        "zippers": "fastening",
        "zip": "fastening",
        "fastenings": "fastening",
        "thread": "construction",
        "threads": "construction",
        "boning": "construction",
    }
    for term, value in category_terms.items():
        if re.search(rf"\b{re.escape(term)}\b", q):
            category = value
            break

    rows = inventory.list_materials(conn)
    for row in rows:
        name = (row["name"] or "").lower()
        if name and re.search(rf"\b{re.escape(name)}\b", q):
            name_contains = row["name"]
            break
        if name == "zip" and re.search(r"\bzipper?s?\b", q):
            name_contains = row["name"]
            break

    colors = {row["color"] for row in rows if row["color"]}
    for value in colors:
        if re.search(rf"\b{re.escape(value.lower())}\b", q):
            color = value
            break

    if name_contains or color or category:
        return inventory.find_materials(conn, category=category, color=color, name_contains=name_contains)
    return rows


def _format_inventory_rows(rows, conn):
    summaries = [inventory.material_summary(conn, row["id"]) for row in rows]
    summaries = [summary for summary in summaries if summary]
    if not summaries:
        return "I couldn't find matching materials in your inventory."
    return "\n".join(
        f"{summary['name']} ({summary['color'] or 'no color'}): "
        f"{summary['available_qty']} {summary['unit']} available, "
        f"{summary['physical_qty']} total, {summary['reserved_qty']} reserved"
        for summary in summaries
    )


def _direct_data_reply(conn, message):
    q = " ".join((message or "").lower().split())
    if not q:
        return None

    order_match = re.search(r"ord-[a-z0-9-]+", q, re.IGNORECASE)
    if order_match:
        order_id = order_match.group(0).upper()
        if re.search(r"(enough fabric|enough material|fabric for|material for)", q):
            return planning.fabric_check(conn, order_id)
        if re.search(r"(needs to be purchased|purchase list|what to buy|buying list)", q):
            return planning.purchase_list(conn, order_id)

    if re.search(r"(what should i work on today|work on today|daily plan)", q):
        return planning.daily_plan(conn)

    if re.search(r"(which order should i prioritize|which order should i prioritise|prioritize order|prioritise order)", q):
        return planning.which_order_first(conn)

    if re.search(r"(list materials|show materials|what materials do i have|how much|what is the stock|stock of|available|qty|quantity|do i have|inventory of|reserves?)", q):
        return _format_inventory_rows(_inventory_rows_for_request(conn, q), conn)

    material = _find_material_match(conn, q)
    if material is not None and re.search(r"(how much|what is the stock|stock of|available|qty|quantity|do i have|inventory of|reserves?)", q):
        summary = inventory.material_summary(conn, material["id"])
        if not summary:
            return f"I couldn't find a stock summary for {material['name']}."
        return summary

    if order_match and re.search(r"(how much|what is the stock|stock of|available|qty|quantity|do i have)", q):
        return planning.fabric_check(conn, order_match.group(0).upper())

    return None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # The registered Google OAuth redirect URI is the app root (see
    # GOOGLE_REDIRECT_URI in .env / agent/google_calendar.py), so the
    # consent-flow callback lands here rather than on a dedicated route.
    code = request.query_params.get("code")
    if code:
        google_calendar.exchange_code(code)
        return RedirectResponse("/")
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(payload: ChatRequest):
    message = (payload.message or "").strip()
    if not message:
        return {"reply": "Please enter a message."}

    conn = get_connection()
    direct_reply = _direct_data_reply(conn, message)
    if direct_reply is not None:
        return {"reply": _stringify_direct_result(direct_reply)}

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        return {
            "reply": "No AI API key is set. Add ANTHROPIC_API_KEY or GEMINI_API_KEY to your environment before chatting."
        }

    client = agent_mod.make_client()
    messages = [{"role": "user", "content": message}]
    try:
        _, reply = agent_mod.run_agent_turn(conn, client, messages)
        return {"reply": reply}
    except Exception as exc:
        if "quota" in str(exc).lower() or "resourceexhausted" in type(exc).__name__.lower():
            return {
                "reply": "The AI service quota is currently exhausted. I can still answer direct inventory and order-data questions, but planning advice needs the AI service available again."
            }
        raise
