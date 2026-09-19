"""AI reasoning/orchestration layer (plan.md Section 11) on top of the
deterministic core. Claude decides which tools to call, reasons across the
results, and explains its recommendations in natural language. It never
touches the database directly — every action goes through tools.dispatch,
which is 100% deterministic Python.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

try:
    import anthropic
except ModuleNotFoundError:  # pragma: no cover - optional if using Gemini only
    anthropic = None

try:
    import google.generativeai as genai
except ModuleNotFoundError:  # pragma: no cover - optional if using Anthropic only
    genai = None

from . import tools

# Model used on the Anthropic path only — GeminiClient reads its own GEMINI_MODEL
# env var independently (see GeminiClient.__init__ below).
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", os.environ.get("TAILORING_AGENT_MODEL", "claude-sonnet-5"))

SYSTEM_PROMPT = """You are the Tailoring Business Agent — an AI production and business \
assistant for a small custom-clothing business run by a college student alongside her studies.

Your job is to understand what the business owner is asking, decide which tools to call \
(possibly several, possibly none), reason across orders, materials, time, and priorities, \
and explain your recommendations clearly and concisely.

Rules you must follow:
- Inventory arithmetic, dates, and any database change are handled by tools, never by your \
own arithmetic. Always call the appropriate tool rather than estimating a number yourself.
- You may recommend and plan freely, but the business owner approves anything significant: \
new orders, material purchases, and schedule changes are fine to propose, but always frame \
them as recommendations, not done deals, unless a tool call has already been made and confirmed.
- When creating a new order, ask for any missing required information (order_id, customer, \
order_type, and ideally deadline/estimated_hours/garment) rather than inventing it.
- When you recommend prioritising or working on something, explain why using the reasons the \
tools return (deadline, material readiness, progress, etc.) — don't just state a conclusion.
- Keep responses grounded only in what the tools actually returned. If a tool reports a \
shortage or conflict, surface it plainly rather than glossing over it.
- The calendar (college commitments) is manual input for now — if the owner mentions a class \
or commitment, use add_commitment to record it rather than asking her to enter it elsewhere.
- Most orders now arrive automatically from her email (agent/email_intake.py) rather than being \
typed here — an ORD-EMAIL-* order you don't recognize is normal, not an error; chat is for \
follow-up questions and corrections, not the primary way orders get entered anymore.
"""


def run_agent_turn(conn, client, messages, max_tool_rounds=8):
    """Runs one user turn to completion (including any tool-use rounds) and
    returns the updated messages list plus the final assistant text."""
    if isinstance(client, GeminiClient):
        response_text = client.generate(messages, conn=conn)
        messages.append({"role": "assistant", "content": response_text})
        return messages, response_text

    for _ in range(max_tool_rounds):
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            tools=tools.TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            final_text = "".join(block.text for block in response.content if block.type == "text")
            return messages, final_text

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = tools.dispatch(conn, block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": _to_text(result),
            })
        messages.append({"role": "user", "content": tool_results})

    return messages, "(Stopped after too many tool-use rounds — something may be looping.)"


def _to_text(result) -> str:
    import json
    return json.dumps(result, default=str)


def extract_text_from_response(response):
    """Convert Gemini's response payloads into plain text without crashing."""
    try:
        text = response.text
        if text:
            return text
    except (AttributeError, TypeError, ValueError):
        pass

    parts = getattr(response, "parts", []) or []
    for part in parts:
        try:
            part_text = part.text
            if part_text:
                return part_text
        except (AttributeError, TypeError, ValueError):
            pass

        try:
            if getattr(part, "function_call"):
                return "The model requested a tool call, but tool execution is not enabled in this chat response path."
        except (AttributeError, TypeError, ValueError):
            pass

    candidates = getattr(response, "candidates", None)
    if candidates:
        try:
            first = candidates[0]
            content = getattr(first, "content", None)
            if content:
                return str(content)
        except Exception:
            pass

    return str(response)


def _extract_function_calls(response):
    """Return any Gemini function_call parts from the response."""
    calls = []
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            fc = getattr(part, "function_call", None)
            if fc is None:
                continue
            name = getattr(fc, "name", None) or getattr(fc, "func_name", None)
            args = getattr(fc, "args", None) or {}
            if name is not None:
                calls.append({"name": name, "args": dict(args) if isinstance(args, dict) else {}})
    return calls


def _tool_declarations_from_specs():
    declarations = []
    for tool in tools.TOOLS:
        spec = tool.get("input_schema", {})
        declarations.append(
            genai.types.content_types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=spec,
            )
        )
    return genai.types.content_types.Tool(function_declarations=declarations)


class GeminiClient:
    def __init__(self):
        if genai is None:
            raise RuntimeError("google-generativeai is not installed. Install it with: pip install google-generativeai")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"),
            system_instruction=SYSTEM_PROMPT,
            tools=_tool_declarations_from_specs(),
        )

    def generate(self, messages, conn=None):
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content")
            if isinstance(text, list):
                text = "\n".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in text
                )
            if text is None:
                continue
            contents.append({
                "role": "user" if role == "user" else "model",
                "parts": [{"text": str(text)}],
            })

        response = self.model.generate_content(contents)
        calls = _extract_function_calls(response)
        if not calls:
            return extract_text_from_response(response)

        if conn is None:
            return "The model requested a tool call, but no database connection was provided."

        tool_results = []
        for call in calls:
            name = call["name"]
            args = call.get("args") or {}
            result = tools.dispatch(conn, name, args)
            tool_results.append({"name": name, "result": result})

        function_response_parts = []
        for item in tool_results:
            function_response_parts.append({
                "function_response": {
                    "name": item["name"],
                    "response": {"result": item["result"]},
                }
            })

        # Reuse Gemini's original model content instead of rebuilding the
        # function_call parts. The original parts contain thought_signature,
        # which Gemini requires on the follow-up request.
        model_content = None
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            model_content = getattr(candidates[0], "content", None)
        if model_content is None:
            return "The model returned a tool call without reusable response content."

        follow_up_contents = contents + [model_content, {
            "role": "user",
            "parts": function_response_parts,
        }]

        follow_up = self.model.generate_content(follow_up_contents)
        return extract_text_from_response(follow_up)


def make_client():
    # Anthropic is preferred whenever it's configured (e.g. after exhausting a
    # Gemini free-tier quota) — Gemini is only used as a fallback.
    if anthropic is not None and os.environ.get("ANTHROPIC_API_KEY"):
        return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    if os.environ.get("GEMINI_API_KEY"):
        return GeminiClient()
    raise RuntimeError("No AI API key found. Set ANTHROPIC_API_KEY or GEMINI_API_KEY.")
