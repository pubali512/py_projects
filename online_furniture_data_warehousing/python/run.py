"""
Online Furniture Data Warehouse - Command-Line Front-End

Usage:
    python python/run.py

Options presented interactively:
    1. Load and transform the database (generate data → run ETL)
    2. Execute an analytical query (choose from Q1–Q8)
"""

import pathlib
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from db import connect

ROOT      = pathlib.Path(__file__).parent.parent
SQL_DIR   = ROOT / "sql" / "analytics"

# =============================================================================
# Analytical question catalogue
# Keys: question ID  →  (description text, SQL file path)
# =============================================================================

QUESTIONS: dict[str, tuple[str, pathlib.Path]] = {
    "Q1": (
        "Revenue and discount by category over time\n"
        "  How does net revenue develop per top-level product category and quarter,\n"
        "  and which category carries the highest discount share?",
        SQL_DIR / "01_Q1_revenue_category.sql",
    ),
    "Q2a": (
        "Average order value by PLZ region (Part A)\n"
        "  Which postal code regions generate the highest average order value?\n"
        "  (order value = sum of net line amounts + shipping cost)",
        SQL_DIR / "02_Q2a_avg_order_value.sql",
    ),
    "Q2b": (
        "Product category mix by PLZ region (Part B)\n"
        "  Does the product category mix differ between postal code regions?",
        SQL_DIR / "03_Q2b_category_mix_region.sql",
    ),
    "Q3a": (
        "Peak order volume by weekday\n"
        "  Which weekdays see the highest order volume across the two-year period?",
        SQL_DIR / "04_Q3a_peak_weekday.sql",
    ),
    "Q3b": (
        "Peak order volume by calendar week (Top 10)\n"
        "  Which calendar weeks see the highest order volume?",
        SQL_DIR / "05_Q3b_peak_calendar_week.sql",
    ),
    "Q4": (
        "Discount effectiveness\n"
        "  Does a higher discount rate correlate with higher quantity sold\n"
        "  or net revenue per order line?",
        SQL_DIR / "06_Q4_discount_effectiveness.sql",
    ),
    "Q5": (
        "Revenue and discount share by price segment\n"
        "  How does revenue and discount compare across Budget (<EUR 200) /\n"
        "  Mid-range (EUR 200-799) / Premium (>=EUR 800) product segments?",
        SQL_DIR / "07_Q5_price_segment.sql",
    ),
    "Q6": (
        "Federal state revenue growth: Year 1 (2024) vs Year 2 (2025)\n"
        "  Which federal states show the strongest revenue growth?",
        SQL_DIR / "08_Q6_state_growth.sql",
    ),
    "Q7": (
        "Supplier revenue by quarter\n"
        "  Which suppliers generate the most net revenue per quarter,\n"
        "  and how has their share shifted over the two-year period?",
        SQL_DIR / "09_Q7_supplier_revenue_quarter.sql",
    ),
    "Q8": (
        "Supplier discount behaviour vs. order volume\n"
        "  Which suppliers' products carry the highest average discount rate,\n"
        "  and does that correlate with order volume?",
        SQL_DIR / "10_Q8_supplier_discount_volume.sql",
    ),
}


# =============================================================================
# Table formatter
# =============================================================================

def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value) if value is not None else "NULL"


def print_table(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("  (no rows returned)")
        return
    headers = list(rows[0].keys())
    data = [[_fmt(r[h]) for h in headers] for r in rows]
    widths = [max(len(h), max(len(d[i]) for d in data)) for i, h in enumerate(headers)]
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    header_row = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    print(sep)
    print(header_row)
    print(sep)
    for row in data:
        print("| " + " | ".join(v.rjust(widths[i]) for i, v in enumerate(row)) + " |")
    print(sep)
    print(f"  {len(rows)} row(s) returned.\n")


# =============================================================================
# Option 1 - Load and transform
# =============================================================================

def option_load() -> None:
    db_path = ROOT / "data" / "furniture.db"
    if db_path.exists():
        answer = input(
            f"\n  Database already exists ({db_path}).\n"
            "  Re-generating will DELETE all existing data.\n"
            "  Continue? (yes/no): "
        ).strip().lower()
        if answer != "yes":
            print("  Aborted.")
            return
        db_path.unlink()
        print()

    print("  Step 1/2 - Generating Business DB data …")
    import importlib
    gen = importlib.import_module("data_gen.generate_data")
    importlib.reload(gen)
    gen.main()

    print("\n  Step 2/2 - Running ETL pipeline …")
    etl_mod = importlib.import_module("etl.run_all_etl")
    importlib.reload(etl_mod)
    etl_mod.run_all_etl()

    print("\n  Database loaded and transformed successfully.")


# =============================================================================
# Option 2 - Execute analytical query
# =============================================================================

def print_question_menu() -> None:
    print("\n  Available analytical questions:")
    print("  " + "-" * 62)
    for key, (description, _) in QUESTIONS.items():
        first_line = description.split("\n")[0]
        print(f"  {key:5s}  {first_line}")
    print("  " + "-" * 62)
    print("  (Enter question ID, e.g. Q1, Q2a, Q-S1)")


def option_query() -> None:
    db_path = ROOT / "data" / "furniture.db"
    if not db_path.exists():
        print("\n  Database not found. Please run option 1 first.")
        return

    print_question_menu()
    choice = input("\n  Select question: ").strip().upper()

    if choice not in QUESTIONS:
        print(f"\n  Unknown question '{choice}'.")
        return

    description, sql_path = QUESTIONS[choice]
    print(f"\n{'='*66}")
    print(f"  {choice} - {description}")
    print(f"{'='*66}\n")

    conn = connect()
    try:
        sql = sql_path.read_text(encoding="utf-8")
        rows = conn.execute(sql).fetchall()
        print_table(rows)
    except sqlite3.OperationalError as exc:
        print(f"  SQL error: {exc}")
    finally:
        conn.close()


# =============================================================================
# Main loop
# =============================================================================

BANNER = r"""
  ╔══════════════════════════════════════════════════════════════╗
  ║     Online Furniture Data Warehouse - CLI                    ║
  ╚══════════════════════════════════════════════════════════════╝
"""

MAIN_MENU = """
  Main menu:
    1  Load and transform the database (generate data + ETL)
    2  Execute an analytical query
    q  Quit
"""


def main() -> None:
    print(BANNER)
    while True:
        print(MAIN_MENU)
        choice = input("  Enter option: ").strip().lower()
        if choice == "1":
            option_load()
        elif choice == "2":
            option_query()
        elif choice in ("q", "quit", "exit"):
            print("\n  Goodbye.\n")
            break
        else:
            print("  Invalid option. Please enter 1, 2, or q.")


if __name__ == "__main__":
    main()
