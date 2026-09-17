## [YYYY-MM-DD HH:MM] Short description of what shipped

- Time spent: 
- Rough tokens used: 
- What shipped: 
- Notes / follow-ups:

## [2026-09-11] Initial project plan

- Time spent: ~30 min (conversation-based, not precisely tracked)
- Rough tokens used: not tracked for this session
- What shipped: `tailoring business agent.md` — full project plan covering overview, 
  core concept, goals/success criteria, MVP vs. final scope, AI-involvement level, 
  data model, build phases, and open questions.
- Notes / follow-ups: Not yet committed to Git — do that next.

## [2026-09-15] Detailed plan finalised (PR #5) + MVP build

- Time spent: not precisely tracked (agent session)
- Rough tokens used: not tracked
- What shipped:
  - `plan.md` expanded to full detailed plan (837 lines, sections 01-28: order types,
    priority system, fractional inventory, sourcing, scheduling, production time
    estimates, Instagram/marketing, Apple Calendar, customer catalogues, agent skills,
    MVP/phased roadmap). Merged via PR #5 on branch `final-detailed-plan`.
  - `agent/` — working MVP implementation of Section 22's scope:
    - Deterministic core: `db.py`, `schema.sql`, `inventory.py`, `orders.py`,
      `scheduling.py`, `priority.py`, `planning.py` (no AI/API key required).
    - AI layer: `tools.py` (15 tool definitions) + `agent.py` (Claude tool-use loop)
      + `cli.py` (chat REPL).
    - `seed_data.py` — example data mirroring the Order #024/#031/#042 scenarios
      already used throughout plan.md.
    - `demo.py` — runs all four MVP core queries with no API key needed; verified
      working end to end.
  - `requirements.txt`, `.gitignore`, `README.md` (setup + usage + design notes).
- Notes / follow-ups:
  - Calendar (college schedule) is manual input for the MVP (`add_commitment`) —
    Apple Calendar integration explicitly deferred, per user decision this session.
  - Chat agent (`cli.py`/`agent.py`) needs `ANTHROPIC_API_KEY` set to run; deterministic
    core (`demo.py`) does not.
  - Not yet committed to Git.
  - Next: decide on committing this, then move to Phase 2 items (shopping-trip
    batching, historical analysis) or real data entry to replace the seed fixtures.
