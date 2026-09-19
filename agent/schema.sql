-- Tailoring Business Agent — MVP schema
-- Mirrors plan.md Sections 05 (Order Data Model), 07 (Materials Inventory),
-- 08 (Material Sourcing), 09 (Scheduling). The calendar itself is the user's
-- actual Google Calendar (Section 14) — there is no local commitments table;
-- agent/google_calendar.py reads/writes it directly.

CREATE TABLE IF NOT EXISTS materials (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    category      TEXT NOT NULL,        -- fabric | trim | fastening | construction | embellishment | packaging
    color         TEXT,
    unit          TEXT NOT NULL,        -- m | spool | pieces | ...
    physical_qty  REAL NOT NULL DEFAULT 0,
    notes         TEXT,                 -- e.g. "previously used for: Corset #024"
    photo_path    TEXT,                 -- e.g. "uploads/materials/MAT-BLACK-COTTON.jpg" under static/ (Section 15: Visual Fabric Inventory)
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Audit trail for every physical quantity change (Section 07: Inventory History)
CREATE TABLE IF NOT EXISTS material_transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id TEXT NOT NULL REFERENCES materials(id),
    delta       REAL NOT NULL,          -- positive = added, negative = consumed
    reason      TEXT NOT NULL,          -- "Purchased" | "Order #024" | "Manual inventory adjustment" | ...
    order_id    TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id                     TEXT PRIMARY KEY,
    customer               TEXT NOT NULL,
    order_type             TEXT NOT NULL,   -- date_restricted | exploratory_available | exploratory_sourcing | alteration
    garment                TEXT,
    description            TEXT,
    deadline               TEXT,            -- ISO date, NULL if flexible
    flexibility            TEXT NOT NULL DEFAULT 'fixed',  -- fixed | flexible
    status                 TEXT NOT NULL DEFAULT 'new',    -- new|planned|in_progress|waiting_material|finishing|completed
    estimated_hours        REAL,
    pickup_delivery_date   TEXT,
    created_at             TEXT NOT NULL DEFAULT (datetime('now')),
    -- Email-driven intake (agent/email_intake.py) — a request detected from
    -- email starts 'pending' until the owner accepts/declines (directly in
    -- the thread, or via a Google Calendar confirmation invite) and is
    -- excluded from scheduling/priority until then (Section 12).
    confirmation_status    TEXT NOT NULL DEFAULT 'confirmed',  -- pending | confirmed
    source                 TEXT NOT NULL DEFAULT 'chat',       -- chat | email
    source_email_thread_id TEXT,
    confirmation_event_id  TEXT,            -- Google Calendar invite event id, while pending
    pending_materials_json TEXT             -- materials extracted from email, applied once confirmed
);

-- One row per Gmail message email_intake.py has already handled, so a poll
-- cycle never reprocesses the same email twice.
CREATE TABLE IF NOT EXISTS processed_emails (
    message_id     TEXT PRIMARY KEY,
    thread_id      TEXT,
    processed_at   TEXT NOT NULL DEFAULT (datetime('now')),
    classification TEXT,   -- new_order | order_reply | supplier_update | irrelevant
    order_id       TEXT
);

-- One production project per order for the MVP (Order -> Project -> Materials -> Inventory, Section 07).
CREATE TABLE IF NOT EXISTS projects (
    id               TEXT PRIMARY KEY,
    order_id         TEXT NOT NULL REFERENCES orders(id),
    stage            TEXT NOT NULL DEFAULT 'design',  -- design|pattern|cutting|construction|finishing|quality_check|completed
    estimated_hours  REAL,
    actual_hours     REAL NOT NULL DEFAULT 0,
    status           TEXT NOT NULL DEFAULT 'not_started'  -- not_started|in_progress|waiting_material|completed
);

-- Project-based material allocation (Section 07: planned vs actual).
CREATE TABLE IF NOT EXISTS project_materials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  TEXT NOT NULL REFERENCES projects(id),
    material_id TEXT NOT NULL REFERENCES materials(id),
    planned_qty REAL NOT NULL,
    actual_qty  REAL,                 -- filled in when usage is recorded
    status      TEXT NOT NULL DEFAULT 'reserved'  -- reserved | consumed
);

-- Logged production time (feeds rescheduling + Section 10/15 historical estimates later).
CREATE TABLE IF NOT EXISTS work_sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(id),
    date       TEXT NOT NULL,   -- ISO date
    hours      REAL NOT NULL,
    stage      TEXT,
    notes      TEXT
);
