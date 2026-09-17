"""Deterministic order + project logic — plan.md Sections 04, 05, 07."""

from . import inventory

ORDER_TYPES = {"date_restricted", "exploratory_available", "exploratory_sourcing", "alteration"}
ORDER_STATUSES = {"new", "planned", "in_progress", "waiting_material", "finishing", "completed"}
PROJECT_STAGES = ["design", "pattern", "cutting", "construction", "finishing", "quality_check", "completed"]


def create_order(
    conn,
    order_id,
    customer,
    order_type,
    garment=None,
    description=None,
    deadline=None,
    estimated_hours=None,
    flexibility="fixed",
    pickup_delivery_date=None,
):
    if order_type not in ORDER_TYPES:
        raise ValueError(f"Unknown order_type: {order_type}. Must be one of {ORDER_TYPES}")
    conn.execute(
        "INSERT INTO orders (id, customer, order_type, garment, description, deadline, "
        "flexibility, estimated_hours, pickup_delivery_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (order_id, customer, order_type, garment, description, deadline, flexibility,
         estimated_hours, pickup_delivery_date),
    )
    # Every order gets exactly one linked project for the MVP (Order -> Project -> Materials).
    project_id = f"PRJ-{order_id}"
    conn.execute(
        "INSERT INTO projects (id, order_id, stage, estimated_hours) VALUES (?, ?, 'design', ?)",
        (project_id, order_id, estimated_hours),
    )
    conn.commit()
    return order_id, project_id


def get_order(conn, order_id):
    return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()


def list_orders(conn, status=None, exclude_completed=False):
    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if exclude_completed:
        query += " AND status != 'completed'"
    query += " ORDER BY deadline IS NULL, deadline"
    return conn.execute(query, params).fetchall()


def update_order_status(conn, order_id, status):
    if status not in ORDER_STATUSES:
        raise ValueError(f"Unknown status: {status}. Must be one of {ORDER_STATUSES}")
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()


def get_project_for_order(conn, order_id):
    return conn.execute("SELECT * FROM projects WHERE order_id = ?", (order_id,)).fetchone()


def allocate_material(conn, project_id, material_id, planned_qty):
    """Reserve a quantity of material for a project. Does NOT touch physical_qty —
    it only reduces *available* qty (reserved is derived, see inventory.reserved_qty)."""
    conn.execute(
        "INSERT INTO project_materials (project_id, material_id, planned_qty, status) "
        "VALUES (?, ?, ?, 'reserved')",
        (project_id, material_id, planned_qty),
    )
    conn.commit()


def required_materials(conn, project_id):
    """Planned materials for a project, each annotated with current availability."""
    rows = conn.execute(
        "SELECT pm.*, m.name, m.color, m.unit FROM project_materials pm "
        "JOIN materials m ON m.id = pm.material_id "
        "WHERE pm.project_id = ?",
        (project_id,),
    ).fetchall()
    result = []
    for row in rows:
        result.append({
            "material_id": row["material_id"],
            "name": row["name"],
            "color": row["color"],
            "unit": row["unit"],
            "planned_qty": row["planned_qty"],
            "actual_qty": row["actual_qty"],
            "status": row["status"],
        })
    return result


def record_material_usage(conn, project_id, material_id, actual_qty):
    """Called when a project finishes using a material: deducts the ACTUAL amount
    from physical stock (Section 07: Automatic Inventory Updates) and closes the reservation."""
    row = conn.execute(
        "SELECT id FROM project_materials WHERE project_id = ? AND material_id = ? AND status = 'reserved'",
        (project_id, material_id),
    ).fetchone()
    if row is None:
        raise ValueError(f"No open reservation for {material_id} on {project_id}")
    order_id = conn.execute("SELECT order_id FROM projects WHERE id = ?", (project_id,)).fetchone()["order_id"]
    conn.execute(
        "UPDATE project_materials SET actual_qty = ?, status = 'consumed' WHERE id = ?",
        (actual_qty, row["id"]),
    )
    conn.commit()
    inventory.adjust_physical(conn, material_id, -actual_qty, f"Order {order_id}", order_id=order_id)


def advance_stage(conn, project_id, new_stage):
    if new_stage not in PROJECT_STAGES:
        raise ValueError(f"Unknown stage: {new_stage}. Must be one of {PROJECT_STAGES}")
    status = "completed" if new_stage == "completed" else "in_progress"
    conn.execute("UPDATE projects SET stage = ?, status = ? WHERE id = ?", (new_stage, status, project_id))
    conn.commit()
    if new_stage == "completed":
        order_id = conn.execute("SELECT order_id FROM projects WHERE id = ?", (project_id,)).fetchone()["order_id"]
        update_order_status(conn, order_id, "completed")


def log_work_session(conn, project_id, date, hours, stage=None, notes=None):
    conn.execute(
        "INSERT INTO work_sessions (project_id, date, hours, stage, notes) VALUES (?, ?, ?, ?, ?)",
        (project_id, date, hours, stage, notes),
    )
    conn.execute(
        "UPDATE projects SET actual_hours = actual_hours + ?, status = 'in_progress' "
        "WHERE id = ? AND status != 'completed'",
        (hours, project_id),
    )
    conn.commit()


def get_project(conn, project_id):
    return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def remaining_hours(conn, project_id):
    project = get_project(conn, project_id)
    if project is None or project["estimated_hours"] is None:
        return None
    return max(0.0, project["estimated_hours"] - project["actual_hours"])
