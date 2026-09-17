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
