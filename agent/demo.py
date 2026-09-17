"""Runs the four MVP core queries against the seeded example data, with no
AI/API key required — proves the deterministic core (Section 22 MVP scope)
works correctly on its own. Run with: python -m agent.demo
"""

import json

from .db import reset_db
from . import seed_data
from . import planning


def main():
    conn = reset_db()
    seed_data.seed(conn)

    print("=" * 70)
    print("QUERY 1: What should I work on today?")
    print("=" * 70)
    print(json.dumps(planning.daily_plan(conn), indent=2))

    print("\n" + "=" * 70)
    print("QUERY 2: Which order should I prioritise?")
    print("=" * 70)
    print(json.dumps(planning.which_order_first(conn), indent=2))

    print("\n" + "=" * 70)
    print("QUERY 3: Do I have enough fabric for ORD-024?")
    print("=" * 70)
    print(json.dumps(planning.fabric_check(conn, "ORD-024"), indent=2))

    print("\n" + "=" * 70)
    print("QUERY 3b: Do I have enough fabric for ORD-031?")
    print("=" * 70)
    print(json.dumps(planning.fabric_check(conn, "ORD-031"), indent=2))

    print("\n" + "=" * 70)
    print("QUERY 4: What needs to be purchased (across all open orders)?")
    print("=" * 70)
    print(json.dumps(planning.purchase_list(conn), indent=2))

    conn.close()


if __name__ == "__main__":
    main()
