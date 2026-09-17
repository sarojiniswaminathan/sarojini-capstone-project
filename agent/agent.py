"""AI reasoning/orchestration layer (plan.md Section 11) on top of the
deterministic core. Claude decides which tools to call, reasons across the
results, and explains its recommendations in natural language. It never
touches the database directly — every action goes through tools.dispatch,
which is 100% deterministic Python.
"""

import os

import anthropic

from . import tools

# Sonnet is the sensible default for this kind of workload (cost-effective, plenty
# capable for tool-orchestration + explanation). Override with TAILORING_AGENT_MODEL.
MODEL = os.environ.get("TAILORING_AGENT_MODEL", "claude-sonnet-5")

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
"""


def run_agent_turn(conn, client, messages, max_tool_rounds=8):
    """Runs one user turn to completion (including any tool-use rounds) and
    returns the updated messages list plus the final assistant text."""
    for _ in range(max_tool_rounds):
        response = client.messages.create(
            model=MODEL,
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


def make_client():
    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
