"""Deterministic inventory logic — plan.md Section 07.

Reserved quantity is *derived* from active project_materials rows (status='reserved'),
never stored directly, so it can never drift from what's actually allocated.
"""

import sqlite3


def add_material(conn, id, name, category, unit, physical_qty=0.0, color=None, notes=None):
    conn.execute(
        "INSERT INTO materials (id, name, category, color, unit, physical_qty, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (id, name, category, color, unit, physical_qty, notes),
    )
    if physical_qty:
        conn.execute(
            "INSERT INTO material_transactions (material_id, delta, reason) VALUES (?, ?, ?)",
            (id, physical_qty, "Initial inventory"),
        )
    conn.commit()


def get_material(conn, material_id) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()


def list_materials(conn):
    return conn.execute("SELECT * FROM materials ORDER BY category, name").fetchall()


def reserved_qty(conn, material_id) -> float:
    row = conn.execute(
        "SELECT COALESCE(SUM(planned_qty), 0) AS total FROM project_materials "
        "WHERE material_id = ? AND status = 'reserved'",
        (material_id,),
    ).fetchone()
    return row["total"]


def available_qty(conn, material_id) -> float:
    material = get_material(conn, material_id)
    if material is None:
        return 0.0
    return material["physical_qty"] - reserved_qty(conn, material_id)


def material_summary(conn, material_id) -> dict:
    """Physical / reserved / available snapshot — the core Section 07 view."""
    material = get_material(conn, material_id)
    if material is None:
        return {}
    reserved = reserved_qty(conn, material_id)
    return {
        "id": material["id"],
        "name": material["name"],
        "color": material["color"],
        "unit": material["unit"],
        "physical_qty": material["physical_qty"],
        "reserved_qty": reserved,
        "available_qty": material["physical_qty"] - reserved,
        "notes": material["notes"],
    }


def adjust_physical(conn, material_id, delta, reason, order_id=None):
    """Record a transaction and update the physical quantity. Used for purchases,
    manual corrections, and actual-usage deductions (never for reservations)."""
    material = get_material(conn, material_id)
    if material is None:
        raise ValueError(f"Unknown material: {material_id}")
    new_qty = material["physical_qty"] + delta
    conn.execute(
        "UPDATE materials SET physical_qty = ?, updated_at = datetime('now') WHERE id = ?",
        (new_qty, material_id),
    )
    conn.execute(
        "INSERT INTO material_transactions (material_id, delta, reason, order_id) VALUES (?, ?, ?, ?)",
        (material_id, delta, reason, order_id),
    )
    conn.commit()
    return new_qty


def manual_correction(conn, material_id, delta, note):
    return adjust_physical(conn, material_id, delta, f"Manual inventory adjustment: {note}")


def material_history(conn, material_id):
    return conn.execute(
        "SELECT * FROM material_transactions WHERE material_id = ? ORDER BY created_at",
        (material_id,),
    ).fetchall()


def find_materials(conn, category=None, color=None, name_contains=None):
    query = "SELECT * FROM materials WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if color:
        query += " AND color = ?"
        params.append(color)
    if name_contains:
        query += " AND name LIKE ?"
        params.append(f"%{name_contains}%")
    return conn.execute(query, params).fetchall()
