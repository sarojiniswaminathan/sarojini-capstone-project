"""Tool definitions bridging the AI reasoning layer to the deterministic core
(plan.md Section 11). Claude decides *which* tool to call and *how to explain*
the result; the tools themselves are 100% deterministic Python.

Google Calendar auth/sync lives in google_calendar.py — add_commitment and
create_order call into it directly, so no tool-level wiring is needed here.
"""

from . import inventory
from . import orders as orders_mod
from . import planning
from . import scheduling

TOOLS = [
    {
        "name": "daily_plan",
        "description": "Answer 'what should I work on today?' — combines open orders, "
                        "priority, material availability, and today's free time into a "
                        "recommended work plan with reasoning and any conflicts found.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "ISO date, defaults to today if omitted"},
            },
        },
    },
    {
        "name": "which_order_first",
        "description": "Answer 'which order should I prioritise?' — ranks all open orders "
                        "by computed priority (deadline, order type, material readiness, progress) "
                        "and explains why the top order was chosen.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "fabric_check",
        "description": "Answer 'do I have enough fabric/material for this order?' — checks every "
                        "material required by the order's project against current available stock.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "e.g. ORD-024"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "purchase_list",
        "description": "Answer 'what needs to be purchased?' — lists material shortages, "
                        "optionally for one order, or combined across ALL open orders if order_id is omitted "
                        "(useful for batching a sourcing trip, Section 08).",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Optional. Omit for all open orders."}},
        },
    },
    {
        "name": "list_orders",
        "description": "List orders, optionally filtered by status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": list(orders_mod.ORDER_STATUSES)},
            },
        },
    },
    {
        "name": "get_order",
        "description": "Get full details of a single order and its linked project.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "create_order",
        "description": "Create a new order (and its linked production project). Use this when the "
                        "business owner describes a new customer request. Ask for any missing required "
                        "info rather than guessing (Section 23).",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "e.g. ORD-050"},
                "customer": {"type": "string"},
                "order_type": {"type": "string", "enum": list(orders_mod.ORDER_TYPES)},
                "garment": {"type": "string"},
                "description": {"type": "string"},
                "deadline": {"type": "string", "description": "ISO date, omit if flexible"},
                "estimated_hours": {"type": "number"},
                "flexibility": {"type": "string", "enum": ["fixed", "flexible"]},
            },
            "required": ["order_id", "customer", "order_type"],
        },
    },
    {
        "name": "allocate_material",
        "description": "Reserve a quantity of a material for an order's project (Section 07).",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "material_id": {"type": "string"},
                "planned_qty": {"type": "number"},
            },
            "required": ["order_id", "material_id", "planned_qty"],
        },
    },
    {
        "name": "list_materials",
        "description": "List all materials in inventory with physical/reserved/available quantities.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "material_summary",
        "description": "Get physical/reserved/available quantity and history summary for one material.",
        "input_schema": {
            "type": "object",
            "properties": {"material_id": {"type": "string"}},
            "required": ["material_id"],
        },
    },
    {
        "name": "add_material",
        "description": "Add a brand-new material to inventory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "material_id": {"type": "string"},
                "name": {"type": "string"},
                "category": {"type": "string"},
                "unit": {"type": "string"},
                "physical_qty": {"type": "number"},
                "color": {"type": "string"},
            },
            "required": ["material_id", "name", "category", "unit"],
        },
    },
    {
        "name": "record_purchase",
        "description": "Record a completed material purchase, increasing physical stock (Section 08).",
        "input_schema": {
            "type": "object",
            "properties": {
                "material_id": {"type": "string"},
                "qty": {"type": "number"},
            },
            "required": ["material_id", "qty"],
        },
    },
    {
        "name": "manual_inventory_correction",
        "description": "Correct inventory to match reality (e.g. 'I found another 0.5m of blue fabric'). "
                        "Always logs a traceable transaction (Section 07).",
        "input_schema": {
            "type": "object",
            "properties": {
                "material_id": {"type": "string"},
                "delta": {"type": "number", "description": "Positive to add, negative to remove."},
                "note": {"type": "string"},
            },
            "required": ["material_id", "delta", "note"],
        },
    },
    {
        "name": "log_work_session",
        "description": "Record production time actually spent on an order today (Section 09 Rescheduling).",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "date": {"type": "string", "description": "ISO date"},
                "hours": {"type": "number"},
                "stage": {"type": "string", "enum": orders_mod.PROJECT_STAGES},
                "notes": {"type": "string"},
            },
            "required": ["order_id", "date", "hours"],
        },
    },
    {
        "name": "add_commitment",
        "description": "Add a college class/exam/other fixed commitment directly to the business "
                        "owner's connected Google Calendar (Section 09/14) — this IS her real calendar, "
                        "there's no separate one. If it isn't connected yet, tell her to connect it "
                        "from the calendar page first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "start_datetime": {"type": "string", "description": "ISO datetime, e.g. 2026-09-16T09:00:00"},
                "end_datetime": {"type": "string"},
                "type": {"type": "string", "enum": ["college", "personal", "blocked"]},
            },
            "required": ["title", "start_datetime", "end_datetime"],
        },
    },
]


def dispatch(conn, name, tool_input):
    if name == "daily_plan":
        return planning.daily_plan(conn, today=tool_input.get("date"))

    if name == "which_order_first":
        return planning.which_order_first(conn)

    if name == "fabric_check":
        return planning.fabric_check(conn, tool_input["order_id"])

    if name == "purchase_list":
        return planning.purchase_list(conn, tool_input.get("order_id"))

    if name == "list_orders":
        rows = orders_mod.list_orders(conn, status=tool_input.get("status"))
        return [dict(r) for r in rows]

    if name == "get_order":
        order = orders_mod.get_order(conn, tool_input["order_id"])
        if order is None:
            return {"error": "Order not found"}
        project = orders_mod.get_project_for_order(conn, tool_input["order_id"])
        materials = orders_mod.required_materials(conn, project["id"]) if project else []
        return {"order": dict(order), "project": dict(project) if project else None, "materials": materials}

    if name == "create_order":
        order_id, project_id = orders_mod.create_order(
            conn,
            tool_input["order_id"],
            customer=tool_input["customer"],
            order_type=tool_input["order_type"],
            garment=tool_input.get("garment"),
            description=tool_input.get("description"),
            deadline=tool_input.get("deadline"),
            estimated_hours=tool_input.get("estimated_hours"),
            flexibility=tool_input.get("flexibility", "fixed"),
        )
        return {"order_id": order_id, "project_id": project_id, "status": "created"}

    if name == "allocate_material":
        project = orders_mod.get_project_for_order(conn, tool_input["order_id"])
        if project is None:
            return {"error": "Order not found"}
        orders_mod.allocate_material(conn, project["id"], tool_input["material_id"], tool_input["planned_qty"])
        return {"status": "allocated"}

    if name == "list_materials":
        rows = inventory.list_materials(conn)
        return [inventory.material_summary(conn, r["id"]) for r in rows]

    if name == "material_summary":
        return inventory.material_summary(conn, tool_input["material_id"])

    if name == "add_material":
        inventory.add_material(
            conn, tool_input["material_id"], tool_input["name"], tool_input["category"],
            tool_input["unit"], physical_qty=tool_input.get("physical_qty", 0.0),
            color=tool_input.get("color"),
        )
        return {"status": "added"}

    if name == "record_purchase":
        new_qty = inventory.adjust_physical(conn, tool_input["material_id"], tool_input["qty"], "Purchased")
        return {"new_physical_qty": new_qty}

    if name == "manual_inventory_correction":
        new_qty = inventory.manual_correction(conn, tool_input["material_id"], tool_input["delta"], tool_input["note"])
        return {"new_physical_qty": new_qty}

    if name == "log_work_session":
        project = orders_mod.get_project_for_order(conn, tool_input["order_id"])
        if project is None:
            return {"error": "Order not found"}
        orders_mod.log_work_session(
            conn, project["id"], tool_input["date"], tool_input["hours"],
            stage=tool_input.get("stage"), notes=tool_input.get("notes"),
        )
        return {"status": "logged", "remaining_hours": orders_mod.remaining_hours(conn, project["id"])}

    if name == "add_commitment":
        event_id = scheduling.add_commitment(
            conn, tool_input["title"], tool_input["start_datetime"], tool_input["end_datetime"],
            type_=tool_input.get("type", "college"),
        )
        if event_id is None:
            return {
                "status": "not_connected",
                "message": "Google Calendar isn't connected yet — connect it from the calendar "
                           "page (top of the page), then try again.",
            }
        return {"status": "added", "google_event_id": event_id}

    return {"error": f"Unknown tool: {name}"}
