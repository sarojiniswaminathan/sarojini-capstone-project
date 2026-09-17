"""Conversational interface (plan.md Section 22: "chat-based, no polished UI needed yet").

Usage:
    python -m agent.cli              # start chatting (requires ANTHROPIC_API_KEY)
    python -m agent.cli --seed       # reset the DB and reload example data first
    python -m agent.cli --fresh      # start from an empty (unseeded) database
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from .db import get_connection, init_db, reset_db, DEFAULT_DB_PATH


def main():
    args = sys.argv[1:]

    if "--seed" in args:
        conn = reset_db()
        from . import seed_data
        seed_data.seed(conn)
        print(f"Reset and seeded database at {DEFAULT_DB_PATH}\n")
    elif "--fresh" in args:
        conn = reset_db()
        print(f"Reset to an empty database at {DEFAULT_DB_PATH}\n")
    else:
        conn = get_connection()
        if not os.path.exists(DEFAULT_DB_PATH):
            init_db(conn)
        else:
            init_db(conn)  # CREATE TABLE IF NOT EXISTS — safe no-op if already set up

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        print("No AI API key is set. The chat agent needs either ANTHROPIC_API_KEY or GEMINI_API_KEY.")
        print("Set it with: export ANTHROPIC_API_KEY=... or export GEMINI_API_KEY=...")
        print("(You can still test the deterministic core with: python -m agent.demo)")
        return

    from . import agent as agent_mod

    client = agent_mod.make_client()
    messages = []

    print("Tailoring Business Agent — type a question or request. Ctrl+C to quit.")
    print("e.g. \"what should I work on today?\", \"do I have enough fabric for ORD-024?\"\n")

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye!")
            break
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break

        messages.append({"role": "user", "content": user_input})
        messages, reply = agent_mod.run_agent_turn(conn, client, messages)
        print(f"\nagent> {reply}\n")


if __name__ == "__main__":
    main()
