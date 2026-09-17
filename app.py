import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from agent.db import get_connection
from agent import agent as agent_mod

app = FastAPI(title="Tailoring Business Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(payload: ChatRequest):
    message = (payload.message or "").strip()
    if not message:
        return {"reply": "Please enter a message."}

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        return {
            "reply": "No AI API key is set. Add ANTHROPIC_API_KEY or GEMINI_API_KEY to your environment before chatting."
        }

    conn = get_connection()
    client = agent_mod.make_client()
    messages = [{"role": "user", "content": message}]
    _, reply = agent_mod.run_agent_turn(conn, client, messages)
    return {"reply": reply}
