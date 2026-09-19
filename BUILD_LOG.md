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

---

## [2026-09-18] - Calendar-centric UI, Google Calendar sync, visual inventory

### 1. Key Metrics
- **Date:** September 18, 2026

### 2. What Shipped
- **Real calendar UI:** The chat-only page was replaced with a calendar-centric page (`templates/index.html`, `static/calendar.js`) built on FullCalendar, fed by a new `GET /calendar/events` endpoint (`calendar_api.py`) that merges local `commitments`, Google Calendar events, and order deadlines into one feed. Clicking a single day opens a details panel (`GET /calendar/day`) with that day's plan, commitments, and any order material shortages.
- **Google Calendar sync (best-effort):** `agent/google_calendar.py` replaces the previously unused, server-unfriendly OAuth stub in `tools.py` (its desktop `run_local_server()` flow didn't fit a running FastAPI process) with a proper web OAuth redirect flow (`/auth/google/login`, `/auth/google/callback`), token persistence to a gitignored `token.json`, and thin wrappers over the Calendar API. `scheduling.add_commitment` and `orders.create_order` call into it directly, so both the chat path and the new direct calendar actions sync for free. Every call fails soft — no Google connection required for the app to work.
- **Visual/ambient inventory (no new page):** A horizontal "glance strip" (`static/inventory.js`, `GET /inventory/glance`) shows every material as a photo/swatch card, color-coded by stock level, with inline photo upload (`POST /inventory/{id}/photo`) and quick +/- corrections (`POST /inventory/{id}/adjust`). Calendar deadline events carry a `shortage` flag so a blocked order's due-date event shows a warning directly on the calendar, instead of a separate inventory screen.
- **Schema + migration:** Added `materials.photo_path` and `commitments.google_event_id` to `agent/schema.sql`; `agent/db.py` now runs a small `PRAGMA table_info`-based migration on every connection so existing local `tailoring.db` files pick up the new columns without a reset.
- **Tests:** `tests/test_calendar_inventory_api.py` covers the shortage flag on `/calendar/events`, `/calendar/day` due-order listing, `/inventory/glance` + `/adjust` (including the 404 path), and the column migration on a pre-existing database.

### 3. Honest Review: What Broke & How Fixed
- **Design decisions surfaced by direct questions, not assumed:** the layout (calendar + floating chat + glance strip), the inventory display (glance strip + calendar badges, explicitly *not* a separate inventory tab), and the day-click interaction (single click, not drag-range) were confirmed with the business owner before writing any frontend code, since all three were genuinely open design choices.
- **Badge timing bug avoided before it shipped:** an initial approach considered marking shortage badges via FullCalendar's `dayCellDidMount` hook, but day-cell mounting and the async event fetch aren't guaranteed to be ordered, which would have made badges flicker or miss on first paint. Switched to rendering the `⚠` warning directly inside the deadline event's own `eventContent`, which ties the badge to the event data that's already loaded correctly.
- **No live Google OAuth credentials in this environment**, so the sync path itself is exercised only via its fail-soft branches (verified with `curl` against `/auth/google/status`, `/calendar/events`, `/inventory/glance`, `/commitments`, `/inventory/.../adjust`) — the actual token exchange and event-creation calls against Google's API are unverified pending a real `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`.

### 4. Current Limitation and Next Step
- Google Calendar sync is one-way and best-effort: local commitments/deadlines are pushed to Google, but edits made directly in Google Calendar for events not created through this app only show up as read-only entries in `/calendar/events` (no update/delete sync back).
- Next step: verify the OAuth flow end-to-end against a real Google Cloud project, and extend sync to logged work sessions (currently only commitments and order deadlines are mirrored).

---

## [2026-09-18b] - Corrected calendar architecture: Google Calendar only, no local mirror

### 1. What Changed
- The business owner clarified she doesn't want a second, separate calendar that merely mirrors Google Calendar — she wants Google Calendar itself to be the one and only calendar. Removed the local `commitments` table (and its `google_event_id` mirror column) entirely from `agent/schema.sql`; `agent/scheduling.py`'s `add_commitment`/`list_commitments` now read from and write to Google Calendar directly via `agent/google_calendar.py`, with no local copy. `agent/seed_data.py` no longer seeds fake local commitments (seeding into someone's real personal calendar isn't appropriate). `/calendar/events` and `/calendar/day` (`calendar_api.py`) now report a `connected` flag so the UI can say plainly "connect Google Calendar" instead of silently showing an empty/stale local calendar.
- **Found and fixed a real bug while doing this:** reading `.env` (already populated with real `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` from earlier setup, contrary to the previous entry's assumption that no credentials existed) showed `GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/`, which did not match the `/auth/google/callback` route the OAuth flow was built against — the "Connect Google Calendar" button would have failed for this exact reason once real credentials were used. Moved the OAuth callback handling into the app's root route (`app.py`) to match the redirect URI that's actually registered, instead of asking the business owner to go change her Google Cloud Console configuration.
- Also swapped the AI provider default to Anthropic-first (`agent/agent.py`), since Gemini free-tier quota had run out; Gemini remains an automatic fallback if `ANTHROPIC_API_KEY` isn't set.

### 2. Honest Review
- The original "best-effort mirror" design was a reasonable reading of "connect to Google Calendar" in isolation, but wrong for what was actually wanted — worth flagging that this was a real rework, not a small tweak, and it's the second time this calendar feature has needed correction based on direct feedback rather than my own assumption.
- Test isolation gap caught during this pass: patching `google_calendar.is_connected` alone would NOT have stopped `create_event`/`list_events` from issuing real requests against a developer's actual Google Calendar if they had already completed the OAuth flow locally (those call `_service()` directly, bypassing `is_connected()`). Fixed by pointing `TOKEN_PATH` at a nonexistent file for the whole test module instead, which forces "not connected" unconditionally regardless of any real local token.
- Still unverified end-to-end: the actual OAuth consent → callback → token exchange against Google's live API (this environment has real client credentials but no completed consent flow / token.json).