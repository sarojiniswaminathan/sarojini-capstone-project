-- Tailoring Business Agent — MVP schema
-- Mirrors plan.md Sections 05 (Order Data Model), 07 (Materials Inventory),
-- 08 (Material Sourcing), 09 (Scheduling). Calendar/commitments are manual
-- user input for the MVP (Apple Calendar integration deferred — Section 14).

CREATE TABLE IF NOT EXISTS materials (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    category      TEXT NOT NULL,        -- fabric | trim | fastening | construction | embellishment | packaging
    color         TEXT,
    unit          TEXT NOT NULL,        -- m | spool | pieces | ...
    physical_qty  REAL NOT NULL DEFAULT 0,
    notes         TEXT,                 -- e.g. "previously used for: Corset #024"
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
    id                    TEXT PRIMARY KEY,
    customer              TEXT NOT NULL,
    order_type            TEXT NOT NULL,   -- date_restricted | exploratory_available | exploratory_sourcing | alteration
    garment                TEXT,
    description            TEXT,
    deadline               TEXT,            -- ISO date, NULL if flexible
    flexibility             TEXT NOT NULL DEFAULT 'fixed',  -- fixed | flexible
    status                  TEXT NOT NULL DEFAULT 'new',    -- new|planned|in_progress|waiting_material|finishing|completed
    estimated_hours         REAL,
    pickup_delivery_date    TEXT,
    created_at              TEXT NOT NULL DEFAULT (datetime('now'))
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

-- Calendar / commitments — manual user input for the MVP (college classes, exams, etc.)
CREATE TABLE IF NOT EXISTS commitments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT NOT NULL,
    start_datetime TEXT NOT NULL,   -- ISO datetime
    end_datetime   TEXT NOT NULL,
    type           TEXT NOT NULL DEFAULT 'college'  -- college | personal | blocked
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
