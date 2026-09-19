"""HTTP endpoints for the email-driven order intake pipeline
(agent/email_intake.py) — a manual trigger for demoing without waiting on
the background poll interval, and a small read endpoint so the UI can show
a "waiting on your response" count without a dedicated page.
"""

from fastapi import APIRouter

from agent import email_intake
from agent import orders as orders_mod
from agent.db import get_connection

router = APIRouter()


@router.post("/email/check-now")
async def check_now():
    conn = get_connection()
    email_intake.poll_and_process(conn)
    email_intake.check_pending_confirmations(conn)
    return {"status": "checked", "pending": len(orders_mod.list_pending_orders(conn))}


@router.get("/orders/pending")
async def pending_orders():
    conn = get_connection()
    rows = orders_mod.list_pending_orders(conn)
    return {
        "orders": [
            {
                "order_id": row["id"],
                "customer": row["customer"],
                "garment": row["garment"],
                "deadline": row["deadline"],
                "source_email_thread_id": row["source_email_thread_id"],
            }
            for row in rows
        ]
    }
