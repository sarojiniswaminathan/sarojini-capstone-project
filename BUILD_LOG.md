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

---

## [2026-09-22] - Deployment config, editor environment, and the start of the OAuth investigation

### 1. Key Metrics
- **Date:** September 22, 2026
- **Time Spent (estimated):** ~1.5 hours — git commits span only 16:40–17:30 (50 min), but that excludes the redirect/deployment discussion, two API-key swaps, and the OAuth troubleshooting that continued after the last commit
- **Approx Tokens Used (estimated):** ~80,000 tokens — dominated by one background research subagent ("explain the email-to-schedule intake flow") that reported exactly 62,514 tokens on completion, plus roughly a dozen file reads/edits and Q&A exchanges for the rest
- **Commits:** `1bd56fa`, `3e1ba9c`, `c114769`

### 2. What Shipped
- **Deployment redirect clarified:** With the app deployed at `https://sarojini-capstone-project-production.up.railway.app/`, established that `GOOGLE_REDIRECT_URI` must match an *Authorized redirect URI* registered on the OAuth client in Google Cloud Console, and that Railway reads its own environment variables — it never sees the local `.env`. Local dev keeps `http://127.0.0.1:8000/`; both URIs can be registered on the same client.
- **API key rotation:** Replaced the `GEMINI_API_KEY` value in `.env`. Verified by grep that the key is read via `os.environ.get("GEMINI_API_KEY")` at every call site (`agent/agent.py`, `agent/email_intake.py`, `app.py`, `agent/cli.py`) and is never hardcoded, so a single `.env` edit is sufficient locally.
- **Insecure-transport allowance for local OAuth (`agent/google_auth.py`):** `oauthlib` refuses to exchange an authorization code over plain `http`, which silently breaks the local (non-HTTPS) redirect. `OAUTHLIB_INSECURE_TRANSPORT` is now set automatically when, and only when, `GOOGLE_REDIRECT_URI` begins with `http://`.
- **Editor environment fix (`.vscode/settings.json`):** Pylance reported `Import "fastapi" could not be resolved` and similar for `pytest`. The packages were present in `.venv` all along; the editor was pointed at the system interpreter. Added `python.defaultInterpreterPath` pointing at `.venv/bin/python`. No application code was involved.
- **Temporary diagnostic instrumentation:** `exchange_code()` was made to write the caught exception and traceback to `oauth_debug.log` so the real OAuth error could be seen at all (removed again the next day once the root cause was found).

### 3. Honest Review: What Broke & How Fixed
- **A failure that was indistinguishable from success:** `POST /email/check-now` returned `{"status":"checked","pending":0}` and the Google consent screen completed without any visible error, yet `token.json` was never created and no email was ever processed. The cause of the invisibility (not yet the cause of the failure itself) was located this session: `exchange_code()` in `agent/google_auth.py` caught *every* exception and returned `False`, and the root route in `app.py` discarded that return value before redirecting. A failed token exchange therefore produced exactly the same user-visible outcome as a successful one.
- **Diagnosis discipline:** rather than continuing to guess at causes (scope mismatch, reused code, redirect mismatch were all considered), instrumentation was added to capture the actual exception. That decision is what produced the answer on 09-23.

### 4. Current Limitation and Next Step
- Google Calendar/Gmail access remained non-functional at the end of this session: `token.json` still did not exist, so `email_intake.poll_and_process()` continued to no-op at its `is_connected()` guard.
- Next step: read `oauth_debug.log` after one more consent attempt and fix whatever the real exchange error turns out to be.

---

## [2026-09-23] - PKCE fix, email intake working end-to-end, and four silent-failure bugs

### 1. Key Metrics
- **Date:** September 23, 2026
- **Time Spent (estimated):** ~3.5 hours — the longest session of the week. Commits span only 16:48–17:27 (39 min), but that captures none of the live debugging before and after: repeated OAuth retries, a `sample`/stack-trace investigation into what turned out to be a slow cold start rather than a hang, several full server restarts each costing 1–3 minutes of cold-start wait, live Gemini API-key testing, and the calendar/email verification loop afterward
- **Approx Tokens Used (estimated):** ~85,000 tokens — a high volume of tool calls (process inspection, `pip`/import probing, verbose import tracing, repeated curl/DB checks), several with long tracebacks or stack-sample output, plus explanatory responses at each bug found
- **Commits:** `644ba91`, `587b2b5`, `fc1af69`, `ea6755a`

### 2. What Shipped
- **PKCE support in the OAuth flow (`agent/google_auth.py`) — the fix that finally produced `token.json`:** the authorization URL now carries a `code_challenge`/`code_challenge_method=S256` derived from a generated verifier, and the same verifier is replayed on the token exchange. Google mandates PKCE for this OAuth client type; the previous code sent neither value. After this change the consent flow completed, `token.json` was written, and `/auth/google/status` reported `{"connected": true}` for the first time.
- **Email intake verified end-to-end:** with a working AI key in place, `poll_and_process()` classified 40 inbox messages and created the first email-sourced order (`ORD-EMAIL-4EF2D6` — customer, garment, and deadline extracted from a plain-language email with no fixed format), then issued a real Google Calendar confirmation invite as the human-in-the-loop approval step.
- **Calendar page redesign, first pass:** sidebar fabric tree rendered from live `/inventory/glance` data (required adding `category` to `material_summary()` in `agent/inventory.py` so the tree can group by it), plus a custom calendar toolbar — prev/next, month and year dropdowns, Month/Week toggle — replacing FullCalendar's default header.
- **`to_rfc3339()` fix (`agent/google_calendar.py`):** date-only values now get a time component.
- **Date-anchored extraction prompt (`agent/email_intake.py`):** the classifier is told today's date and instructed to resolve a bare month/day to the nearest future occurrence.
- **`watchfiles` added to `requirements.txt`.**

### 3. Honest Review: What Broke & How Fixed
- **OAuth: `invalid_grant — Missing code verifier`.** The instrumentation added on 09-22 produced the actual error immediately. Google required PKCE; the app never sent it. Every consent attempt across two days had been failing at the final token-exchange step while presenting a completely clean consent screen. Fixed as described above, and the debug logging was removed.
- **AI classification was failing on every single email.** `GEMINI_API_KEY` held a key that Google was actively blocking for this API (`API_KEY_SERVICE_BLOCKED` / `PERMISSION_DENIED` on `generativelanguage.googleapis.com`) — it was an API-restricted key, not a general Gemini key. Because `poll_and_process()` wraps each message in `except Exception: continue`, all 20 candidate messages failed and were skipped without ever being marked processed, so the endpoint kept reporting `"checked", pending 0`. Replaced with a working key. Worth recording that the two `GEMINI_API_KEY*` variables had been mentally labelled "CalendarAPI" and "GmailAPI" in `.env`, but the code uses them for exactly one thing — Gemini email classification. Calendar and Gmail *access* is OAuth, entirely separate.
- **Every Google Calendar event was invisible in the app's own calendar.** `to_rfc3339("2026-09-23")` returned `"2026-09-23Z"` — a date with a timezone marker but no time — which the Calendar API rejects with HTTP 400. `list_events()` catches `HttpError` and returns `[]`, so `/calendar/events` had been quietly returning local order deadlines only, for every date range, since the feature was built. Confirmed by reproducing the 400 directly against the API before and after the fix.
- **The dev server appeared to hang completely** — `/health` itself timed out, repeatedly, for minutes. Cause: `uvicorn --reload` had fallen back to `StatReload` (because `watchfiles` was not installed), which polls file timestamps across the entire project tree — including `.venv`'s ~17,000 files. Installing `watchfiles` switched it to event-based watching.
- **Genuinely slow cold start, misdiagnosed twice as a deadlock.** Importing `anthropic` and `google-generativeai` walks thousands of small module files, and this project lives inside an iCloud-synced Desktop folder, so per-file overhead is high; a fresh start takes roughly 30–90 seconds. Two separate "the process is hung" conclusions during this session were wrong — a `sample` stack trace showed the process sitting in a normal `kevent` event-loop wait, i.e. already serving. The lesson recorded here: a 10-second timeout is not evidence of a deadlock in this environment.
- **Black "busy day" cells made the real calendar unreadable and were reverted.** The reference mockup shows two solid dark cells in an otherwise empty month; filling a cell for *any* event turned a real week of college classes, order deadlines, and flights into dark-on-dark text. Removed the same day it shipped.
- **Deadline extracted with the wrong year:** "Oct 10th" became `2024-10-10`. The prompt gave the model no reference date. Fixed by injecting today's date plus an explicit nearest-future-occurrence rule; the existing order's deadline was corrected to `2026-10-10`.
- **The common thread:** four of these — the OAuth exchange, the blocked AI key, the calendar 400, and the original email no-op — were all the same failure shape. A broad `except` swallowed a real error, and the resulting silence was indistinguishable from "there was nothing to do." Fail-soft is the right design for an unattended poll loop, but without a log line it makes debugging nearly impossible from the outside.

### 4. Current Limitation and Next Step
- `ORD-EMAIL-4EF2D6` is still `pending`: the Google Calendar confirmation invite has been created and delivered, but the RSVP has not been answered, so the accept → `confirmed` half of `check_pending_confirmations()` remains unverified end-to-end.
- The app does not auto-confirm from the text of an owner's email reply; approval is deliberately routed through the calendar invite. This surprised the owner during testing and is worth stating plainly in the README.
- Intake is polling-based at `EMAIL_POLL_INTERVAL_SECONDS` (default 180s), with `POST /email/check-now` as the manual trigger. No Gmail push notifications.
- The fail-soft `except` blocks should log the swallowed exception rather than discarding it.

---

## [2026-09-24] - Design-token rebuild of the calendar page

### 1. Key Metrics
- **Date:** September 24, 2026
- **Time Spent (estimated):** ~1.25 hours — a single focused pass with no server restarts required (no Python files changed), a design-scope clarification exchange, then a full rewrite of `style.css`/`index.html`/`inventory.js` plus a new `layout.js`
- **Approx Tokens Used (estimated):** ~35,000 tokens — the largest share is the design spec itself (received twice, duplicated) and the full-file rewrites of `static/style.css` (the biggest single file in the change) and `templates/index.html`, plus verification curl calls
- **Commit:** `edd0ad3`

### 2. What Shipped
- **A single token set (`static/style.css`)** — typography (Inter 400/500/600 with the specified scale, letter-spacing, and tabular-nums day numbers), colors, the 4px-base spacing values, radii, and the two shadow definitions — declared once as CSS custom properties and referenced everywhere, replacing the previous ad-hoc values.
- **Title bar (`templates/index.html`):** a single 42px full-width surface with decorative, `aria-hidden` traffic lights and the application title, with the Google-connection status and pending-order badge folded into it so no existing function was lost.
- **Sidebar:** 250px, right-cast shadow only, 47px category rows with the specified chevron/label indents and 8px-inset dividers, an animated accordion, and a working collapse toggle (`static/layout.js`) with an `aria-expanded` state and a ⌘B / Ctrl+B shortcut.
- **Leaf items restructured to match the reference layout:** label above a 93 × 93 swatch rather than beside it. Materials with no colour (`Boning`, `Zip`) render as plain 36px label rows.
- **Calendar card:** specified outer margins, inner padding, 30px header row, 28px selects with a custom chevron, caption-styled weekday row, day numbers positioned per spec, no "today" highlight, and a 100ms hover fill.
- **Accessibility and motion:** `:focus-visible` rings on interactive elements, `prefers-reduced-motion` honoured, and the ≥1280 / 768–1280 / <768 responsive tiers.

### 3. Honest Review: What Broke & How Fixed
- **Two scope decisions were referred back to the owner rather than assumed**, because both were larger than a restyle. First, the reference is in substance a *date-range picker* — its two dark cells are a range start and end, with a lighter fill between — whereas this application's calendar displays real orders, deadlines, and Google events. Matching it literally would have replaced a working feature with a different one. Second, the accompanying specification called for React, TypeScript, Tailwind, shadcn/ui, and Playwright "if there isn't an existing stack"; there is one (FastAPI, Jinja2, vanilla JS, FullCalendar), so adopting that toolchain would have meant introducing Node to a Python repository and discarding the working Google Calendar integration. The owner chose to keep the existing stack and the existing event calendar.
- **Drag-and-drop was deliberately not implemented.** The specification asks for inventory items to be draggable onto calendar cells, but with the range-picker semantics declined there is no defined behaviour for a drop, and no backend operation it would correspond to. A `cursor: grab` style that had been added reflexively was removed, since it advertises an interaction that does not exist.
- **Verification was done by inspection and live endpoint checks, not by automated screenshot comparison.** The specification asks for a Playwright screenshot diff at 1372 × 891; Playwright requires Node, which this repository does not have and which the owner chose not to add. Pixel-level conformance is therefore claimed only as "matched by eye against the reference," which is weaker evidence and is recorded as such.
- **Content was taken from the repository, not the mockup.** The tree renders the real seven materials under their real categories (`fabric`, `construction`, `fastening`); the mockup's `Cotton → Blue / Orange` three-level nesting was not reproduced, because the real data has no material carrying multiple colour variants and inventing that level would have misrepresented the inventory. The window title likewise remains the application's own name rather than the mockup's.

### 4. Current Limitation and Next Step
- No automated visual regression test exists for the page; any future CSS change can silently break the layout.
- The sidebar's `<768px` overlay drawer opens by default on first load at that width rather than starting closed, which is a minor deviation on the least-used breakpoint.
- Next step: confirm the rendered page against the reference in a browser and correct any remaining spacing or colour differences.