# Capstone Build Log — Tailoring Business Agent

## [2026-09-10] - Assessment 1: System Architecture, Data Schema & AI Strategy

### 1. Key Metrics
- **Date:** September 10, 2026
- **Time Spent:** 3.0 Hours
- **Approx Tokens Used:** ~12,000 tokens

### 2. What Shipped
- **Core Architecture & Schema:** Designed and deployed SQLite database models (`agent/schema.sql`, `agent/db.py`) handling three core tailoring order types: `date_restricted`, `exploratory_sourcing`, and `alterations`.
- **Fractional Inventory Model:** Built `agent/inventory.py` to support explicit tracking across `physical_qty`, `reserved_qty`, and `available_qty` to prevent inventory double-booking.
- **Academic Calendar Integration:** Created initial seed datasets (`data/college_calendar.json` and `data/inventory.json`) to map college conflict awareness against production labor hours.
- **AI-vs-Deterministic Execution Strategy:** Established a strict system split where price and inventory calculations remain deterministic while intent parsing and priority scoring are handled by AI.
- **Git & Environment Security:** Configured `.gitignore` to protect sensitive local OAuth client secrets and user calendar tokens (`credentials.json`).

### 3. Honest Review: What Broke & How Fixed
- **Documentation Path Mismatch:** Initial project logs referenced an external file named `tailoring business agent.md`, which created path mismatches and left `BUILD_LOG.md` unpopulated in the repository root.
- **How Fixed:** Removed references to `tailoring business agent.md`, standardized all capstone documentation, and consolidated all build history directly inside `BUILD_LOG.md`.

---

## [2026-09-17] - Assessment 2: Agent Loop, Deterministic Tools & Web App
### 1. Key Metrics
- **Date:** September 17, 2026
- **Time Spent:** 8+ hours
- **Approx Tokens Used:** ~22,000 tokens

### 2. What Shipped and Was Verified
- **Deterministic business core:** SQLite-backed inventory, orders, projects, material reservations, purchasing shortages, priority ranking, daily planning, and scheduling logic are implemented in `agent/inventory.py`, `agent/orders.py`, `agent/planning.py`, `agent/priority.py`, and `agent/scheduling.py`.
- **Tool registry and agent loop:** `agent/tools.py` exposes deterministic business operations to the orchestration layer. `agent/agent.py` supports an AI turn followed by tool dispatch and a final response, with Gemini function-call parsing and follow-up responses.
- **FastAPI web app:** `app.py` serves the browser interface and `/chat` endpoint at `http://127.0.0.1:8000`. The UI is implemented with `templates/index.html` and `static/app.js`.
- **Direct-data-first routing:** Basic inventory and order-data questions are answered from SQLite before an AI client is created. This keeps factual stock checks available when no AI key is present or when the AI quota is exhausted.
- **Request-specific inventory filtering:** Inventory responses now filter by the requested category, material, color, and common synonyms. For example, fabric questions return fabric only, and “zippers” matches the stored material named `Zip` without displaying unrelated stock.
- **Direct planning paths:** Daily-plan, prioritization, order-material checks, and order purchase-list questions use deterministic planning functions before the AI fallback.
- **Environment and redirect configuration:** `.env` is loaded with `python-dotenv`, and the local Google redirect configuration was standardized around `http://127.0.0.1:8000`.
- **Regression coverage:** `tests/test_direct_data_routing.py` verifies that inventory questions bypass AI and that fabric-only and zipper-only requests exclude unrelated materials.

### 3. Corrections to Earlier Description
- The active web framework is **FastAPI with Uvicorn**, not Streamlit.
- The configured Gemini model is **`gemini-3.6-flash` by default**, with `GEMINI_MODEL` available as an override; the earlier `gemini-2.5-flash` description was outdated.
- The current repository contains a Google Calendar OAuth helper and manual commitment scheduling, but this assessment does not claim a verified Google Calendar MCP connector or Filesystem MCP connector.
- The current repository does not contain a verified `allocate_materials_and_estimate_hours` custom skill by that exact name. Material allocation and hour estimation are implemented through the deterministic inventory, orders, planning, and scheduling modules.

### 4. Honest Review: What Broke and How It Was Fixed
- **Standalone module execution:** Running `python3 agent/demo.py` directly caused relative-import errors. The supported package invocation is `python -m agent.demo`.
- **Gemini response handling:** Gemini function-call responses did not initially convert cleanly into the agent loop. Function-call extraction, deterministic tool dispatch, and follow-up response construction were added in `agent/agent.py`.
- **Chat failures:** The browser displayed “Something went wrong while contacting the server” when `/chat` returned HTTP 500. Investigation traced the final runtime failure to Gemini free-tier quota exhaustion (`ResourceExhausted`, limit 20 requests for `gemini-3.6-flash`).
- **AI dependency for simple facts:** The chat endpoint previously created the AI client for every message. A direct-data-first route was added in `app.py`, so routine inventory questions do not consume API quota.
- **Over-broad inventory responses:** Generic inventory matching initially returned every material, even when the request asked only for fabric or zippers. Category, name, color, and synonym filtering now limits the response to the requested information.
- **Stale local server process:** Changes were not visible while an older Uvicorn process still occupied port 8000. Restarting the process loaded the current code and restored the expected behavior.

### 5. Current Limitation and Next Step
- AI-dependent conversational questions still require an available Gemini or Anthropic API key. When Gemini quota is exhausted, the web app now returns a clear message instead of an HTTP 500, while direct inventory and order-data questions continue to work locally.
- The next assessment step is to broaden deterministic intent matching and add tests for order-specific material checks, purchase lists, and planning responses without weakening the direct-data-first boundary.