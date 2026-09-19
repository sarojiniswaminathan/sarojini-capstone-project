"""Example data mirroring the scenarios used throughout plan.md, so the MVP
is demonstrable immediately. Replace with real data whenever ready — this is
just a starting fixture, not a hardcoded assumption.

There's no local commitments/college-calendar fixture here: the calendar is
the business owner's actual Google Calendar (Section 14), and seeding can't
(and shouldn't) write into someone's real personal calendar."""

from datetime import date, timedelta

from . import inventory
from . import orders as orders_mod


def seed(conn):
    today = date.today()

    # --- Materials (Section 07) ---
    inventory.add_material(conn, "MAT-BLACK-COTTON", "Cotton", "fabric", "m", 4.75, color="Black")
    inventory.add_material(conn, "MAT-BLACK-DENIM", "Denim", "fabric", "m", 3.20, color="Black")
    inventory.add_material(conn, "MAT-RED-SATIN", "Satin", "fabric", "m", 0.0, color="Red")
    inventory.add_material(conn, "MAT-LINING", "Lining", "fabric", "m", 2.0, color="White")
    inventory.add_material(conn, "MAT-BONING", "Boning", "construction", "pieces", 20)
    inventory.add_material(conn, "MAT-ZIP", "Zip", "fastening", "pieces", 8)
    inventory.add_material(conn, "MAT-THREAD-BLACK", "Thread", "construction", "spool", 2.0, color="Black")

    # --- Order #024: Black Corset (date-restricted, materials available) ---
    _, prj_024 = orders_mod.create_order(
        conn, "ORD-024", customer="Aisha", order_type="date_restricted",
        garment="Corset", description="Black boned corset",
        deadline=(today + timedelta(days=5)).isoformat(), estimated_hours=10,
    )
    orders_mod.allocate_material(conn, prj_024, "MAT-BLACK-DENIM", 1.80)
    orders_mod.allocate_material(conn, prj_024, "MAT-LINING", 1.20)
    orders_mod.allocate_material(conn, prj_024, "MAT-BONING", 6)
    orders_mod.allocate_material(conn, prj_024, "MAT-ZIP", 1)
    orders_mod.allocate_material(conn, prj_024, "MAT-THREAD-BLACK", 0.20)
    orders_mod.update_order_status(conn, "ORD-024", "planned")

    # --- Order #031: Red satin dress (date-restricted, needs sourcing) ---
    _, prj_031 = orders_mod.create_order(
        conn, "ORD-031", customer="Meera", order_type="exploratory_sourcing",
        garment="Dress", description="Flowy red satin dress",
        deadline=(today + timedelta(days=12)).isoformat(), estimated_hours=7,
    )
    orders_mod.allocate_material(conn, prj_031, "MAT-RED-SATIN", 3.2)
    orders_mod.update_order_status(conn, "ORD-031", "waiting_material")

    # --- Order #042: Fitted top + skirt (date-restricted, far out) ---
    _, prj_042 = orders_mod.create_order(
        conn, "ORD-042", customer="Priya", order_type="date_restricted",
        garment="Top + Skirt", description="Fitted dark-colour two-piece",
        deadline=(today + timedelta(days=20)).isoformat(), estimated_hours=9,
    )
    orders_mod.allocate_material(conn, prj_042, "MAT-BLACK-COTTON", 2.8)
    orders_mod.update_order_status(conn, "ORD-042", "planned")

    conn.commit()


if __name__ == "__main__":
    from .db import reset_db
    conn = reset_db()
    seed(conn)
    print("Seeded tailoring.db with example orders, materials, and commitments.")
