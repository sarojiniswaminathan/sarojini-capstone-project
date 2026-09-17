"""Dynamic priority scoring — plan.md Section 06.

Priority is *computed*, not stored, so it's always recalculated from current
deadline/materials/progress rather than going stale (Section 06: "Priority Is
Not Static").
"""

from datetime import date

from . import orders as orders_mod
from . import inventory

ORDER_TYPE_WEIGHT = {
    "date_restricted": 3,
    "alteration": 2,
    "exploratory_available": 1,
    "exploratory_sourcing": 0,
}


def materials_ready(conn, project_id):
    """True if every planned material for this project is fully available (no shortage)."""
    for item in orders_mod.required_materials(conn, project_id):
        if item["status"] != "reserved":
            continue
        summary = inventory.material_summary(conn, item["material_id"])
        # planned_qty for this project is already included in "reserved", so a material
        # is short only if physical stock can't cover ALL current reservations of it.
        if summary["physical_qty"] < summary["reserved_qty"]:
            return False
    return True


def compute_priority(conn, order_id, today=None):
    """Returns {score, reasons: [...]} — a numeric score plus a human-readable
    explanation, since Section 06 requires the agent to explain *why*."""
    today = today or date.today()
    order = orders_mod.get_order(conn, order_id)
    if order is None:
        raise ValueError(f"Unknown order: {order_id}")
    project = orders_mod.get_project_for_order(conn, order_id)

    reasons = []
    score = 0.0

    # 1. Deadline urgency — closer deadline = higher score, dominates the ranking.
    if order["deadline"]:
        deadline = date.fromisoformat(order["deadline"])
        days_left = (deadline - today).days
        urgency = max(0.0, 100.0 - days_left)  # e.g. 5 days left -> 95
        score += urgency
        reasons.append(f"Deadline in {days_left} day(s) ({order['deadline']}) -> urgency {urgency:.0f}")
    else:
        reasons.append("No fixed deadline -> no urgency contribution")

    # 2. Order type weight
    type_weight = ORDER_TYPE_WEIGHT.get(order["order_type"], 0) * 5
    score += type_weight
    reasons.append(f"Order type '{order['order_type']}' -> +{type_weight}")

    # 3. Material readiness — sourcing-blocked work can't start, so it's deprioritised
    #    relative to ready work even if its deadline is closer.
    ready = materials_ready(conn, project["id"]) if project else True
    if ready:
        score += 10
        reasons.append("All required materials available -> +10 (can start now)")
    else:
        score -= 20
        reasons.append("Missing required materials -> -20 (blocked on sourcing)")

    # 4. Progress — an almost-finished project should usually be finished first.
    if project and project["estimated_hours"]:
        fraction_done = min(1.0, project["actual_hours"] / project["estimated_hours"])
        progress_bonus = fraction_done * 15
        score += progress_bonus
        reasons.append(f"{fraction_done * 100:.0f}% complete -> +{progress_bonus:.1f}")

    return {"order_id": order_id, "score": round(score, 1), "materials_ready": ready, "reasons": reasons}


def rank_orders(conn, today=None, exclude_completed=True):
    open_orders = orders_mod.list_orders(conn, exclude_completed=exclude_completed)
    ranked = [compute_priority(conn, o["id"], today=today) for o in open_orders]
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked
