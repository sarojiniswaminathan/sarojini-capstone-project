"""Orchestration for the four MVP core reasoning queries (plan.md Section 22):

  1. What should I work on today?
  2. Which order should I prioritise?
  3. Do I have enough fabric for this order?
  4. What needs to be purchased for order X?

These are deterministic — no AI judgement required to get a correct answer —
per the split in Section 11. The agent (agent.py) calls these as tools and
uses AI only to phrase the natural-language response and hold the conversation.
"""

from datetime import date

from . import orders as orders_mod
from . import inventory
from . import priority as priority_mod
from . import scheduling


def fabric_check(conn, order_id):
    """Query 3: Do I have enough fabric/material for this order?"""
    order = orders_mod.get_order(conn, order_id)
    if order is None:
        return {"error": f"Unknown order: {order_id}"}
    project = orders_mod.get_project_for_order(conn, order_id)
    required = orders_mod.required_materials(conn, project["id"])

    lines = []
    all_ready = True
    for item in required:
        summary = inventory.material_summary(conn, item["material_id"])
        # Available *excluding this order's own reservation* is what matters when
        # checking "do I have enough", since the reservation already accounts for it.
        available_excluding_this = summary["available_qty"] + item["planned_qty"] if item["status"] == "reserved" else summary["available_qty"]
        shortage = max(0.0, item["planned_qty"] - available_excluding_this)
        ready = shortage <= 0
        all_ready = all_ready and ready
        lines.append({
            "material": item["name"],
            "color": item["color"],
            "unit": item["unit"],
            "required_qty": item["planned_qty"],
            "available_qty_excluding_reservation": round(available_excluding_this, 2),
            "shortage": round(shortage, 2),
            "ready": ready,
        })
    return {"order_id": order_id, "all_materials_available": all_ready, "materials": lines}


def purchase_list(conn, order_id=None):
    """Query 4: What needs to be purchased (for one order, or all open orders combined)?"""
    order_ids = [order_id] if order_id else [o["id"] for o in orders_mod.list_orders(conn, exclude_completed=True)]
    combined = {}  # material_id -> {name, unit, shortage, orders: [...]}
    for oid in order_ids:
        check = fabric_check(conn, oid)
        if "error" in check:
            continue
        for item in check["materials"]:
            if item["shortage"] <= 0:
                continue
            key = item["material"] + "|" + str(item["color"])
            entry = combined.setdefault(key, {
                "material": item["material"], "color": item["color"], "unit": item["unit"],
                "total_shortage": 0.0, "orders": [],
            })
            entry["total_shortage"] = round(entry["total_shortage"] + item["shortage"], 2)
            entry["orders"].append(oid)
    return list(combined.values())


def which_order_first(conn, today=None):
    """Query 2: Which order should I prioritise?"""
    ranked = priority_mod.rank_orders(conn, today=today)
    if not ranked:
        return {"message": "No open orders."}
    top = ranked[0]
    order = orders_mod.get_order(conn, top["order_id"])
    return {
        "recommended_order_id": top["order_id"],
        "customer": order["customer"],
        "garment": order["garment"],
        "score": top["score"],
        "reasons": top["reasons"],
        "full_ranking": ranked,
    }


def daily_plan(conn, today=None, available_hours_override=None):
    """Query 1: What should I work on today?

    Pulls from orders+priority+materials+time in one pass, per Section 02/11.
    """
    today = today or date.today()
    if isinstance(today, str):
        today = date.fromisoformat(today)

    ranked = priority_mod.rank_orders(conn, today=today)
    if not ranked:
        return {"message": "No open orders — nothing to plan.", "date": today.isoformat()}

    today_schedule = scheduling.free_blocks_today(conn, today=today)
    available_today = available_hours_override if available_hours_override is not None else today_schedule["free_hours"]

    recommendations = []
    hours_left_today = available_today
    conflicts = []

    for entry in ranked:
        if hours_left_today <= 0:
            break
        order = orders_mod.get_order(conn, entry["order_id"])
        project = orders_mod.get_project_for_order(conn, entry["order_id"])
        remaining = orders_mod.remaining_hours(conn, project["id"]) if project else None

        if not entry["materials_ready"]:
            conflicts.append({
                "order_id": entry["order_id"],
                "issue": "Blocked on missing materials — see purchase_list for what's needed.",
            })
            continue

        if order["deadline"] and remaining:
            check = scheduling.conflict_check(conn, project["id"], order["deadline"], remaining)
            if check["has_conflict"]:
                conflicts.append({
                    "order_id": entry["order_id"],
                    "issue": (f"Only {check['available_hours']}h available before deadline "
                              f"{order['deadline']}, but {remaining}h of work remain "
                              f"(short by {check['shortfall_hours']}h)."),
                })

        session_hours = min(hours_left_today, remaining) if remaining else hours_left_today
        if session_hours <= 0:
            continue
        recommendations.append({
            "order_id": entry["order_id"],
            "customer": order["customer"],
            "garment": order["garment"],
            "suggested_hours": round(session_hours, 2),
            "priority_score": entry["score"],
            "why": entry["reasons"],
        })
        hours_left_today -= session_hours

    return {
        "date": today.isoformat(),
        "available_hours_today": available_today,
        "free_blocks": today_schedule["free_blocks"],
        "recommendations": recommendations,
        "conflicts": conflicts,
    }
