"""
Online Furniture Data Warehouse - Command-Line Front-End

Usage:
    python python/run.py

Options presented interactively:
    1. Generate Business DB  (Faker -- source tables only)
    2. Run ETL pipeline      (DWH only -- reads existing Business DB, read-only)
    3. Full pipeline         (generate + ETL in one step)
    4. Execute an analytical query (Q1-Q8)
    5. Generate demo delta   (new suppliers/products/customers/orders + SCD 2 address changes)
"""

import pathlib
import sqlite3
import sys

# sys.path.insert(0, str(pathlib.Path(__file__).parent))

from db import connect
from data_gen.generate_data import main as gen_main
from data_gen.generate_incremental_data import main as delta_main
from etl.run_all_etl import run_all_etl as etl_main

ROOT      = pathlib.Path(__file__).parent.parent
SQL_DIR   = ROOT / "sql" / "analytics"

# =============================================================================
# Analytical question catalogue
# Keys: question ID  ->  (description text, SQL file path)
# =============================================================================

QUESTIONS: dict[str, tuple[str, pathlib.Path]] = {
    "Q1": (
        "Revenue and Discount by category over time\n"
        "  How does net revenue as well as Discounts develop per top-level product\n"
        "  category and Quarter?",
        SQL_DIR / "01_Q1_revenue_category.sql",
    ),
    "Q2": (
        "Top 10 PLZ zones by net revenue\n"
        "  Which 10 postal code zones (first 2 digits of PLZ) generate\n"
        "  the maximum net revenue?",
        SQL_DIR / "02_Q2_top_plz_zones.sql",
    ),
    "Q3": (
        "Top 2 product categories per federal state by net revenue\n"
        "  What are the two highest net revenue generating product\n"
        "  categories per federal state?",
        SQL_DIR / "03_Q3_top_categories_per_state.sql",
    ),
    "Q4": (
        "Peak order volume by Weekday\n"
        "  Which weekdays see the highest order volume across the two-Year period?",
        SQL_DIR / "04_Q4_peak_weekday.sql",
    ),
    "Q5": (
        "Peak order volume by calendar week (Top 10)\n"
        "  Which calendar weeks see the highest order volume?",
        SQL_DIR / "05_Q5_peak_calendar_week.sql",
    ),
    "Q6": (
        "Revenue and Discount share by price segment\n"
        "  How does revenue and Discount compare across Budget (<EUR 200) /\n"
        "  Mid-range (EUR 200-799) / Premium (>=EUR 800) product segments?",
        SQL_DIR / "06_Q6_price_segment.sql",
    ),
    "Q7": (
        "Federal state revenue growth: Year 1 (2024) vs Year 2 (2025)\n"
        "  Which federal states show the strongest revenue growth?",
        SQL_DIR / "07_Q7_state_growth.sql",
    ),
    "Q8": (
        "Top 3 suppliers by net revenue per quarter\n"
        "  Which 3 suppliers generate the most net revenue per Quarter?",
        SQL_DIR / "08_Q8_top3_suppliers_per_quarter.sql",
    ),
    "Q9": (
        "Supplier Discount behaviour vs. order volume\n"
        "  Which suppliers' products carry the highest average Discount rate,\n"
        "  and does that correlate with order volume?",
        SQL_DIR / "09_Q9_supplier_discount_volume.sql",
    ),
}


# =============================================================================
# Table formatter
# =============================================================================

def _fmt(value, col: str = "") -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int) and col.lower() != "year":
        return f"{value:,}"
    return str(value) if value is not None else "NULL"


def print_table(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("  (no rows returned)")
        return
    headers = list(rows[0].keys())
    data = [[_fmt(r[h], h) for h in headers] for r in rows]
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
# Option 1 -- Generate Business DB (source tables only)
# =============================================================================

def option_generate() -> None:
    """Delete the database file and regenerate Business DB source tables via Faker."""
    db_path = ROOT / "data" / "furniture.db"
    if db_path.exists():
        answer = input(
            f"\n  Business DB already exists ({db_path.name}).\n"
            "  This will DELETE all existing data (source tables AND DWH).\n"
            "  Continue? (yes/no): "
        ).strip().lower()
        if answer != "yes":
            print("  Aborted.")
            return
        db_path.unlink()
        print()

    print("  Generating Business DB (Faker) ...")
    gen_main()
    print("\n  Business DB created. Run option 2 to populate the DWH.")


# =============================================================================
# Option 2 -- Run ETL pipeline (DWH only -- does not touch source tables)
# =============================================================================

def option_etl() -> None:
    """Run the ETL pipeline on the existing Business DB. Source tables are read-only."""
    db_path = ROOT / "data" / "furniture.db"
    if not db_path.exists():
        print("\n  Business DB not found. Run option 1 first to generate source data.")
        return

    print("  Running ETL pipeline ...")
    etl_main()
    print("\n  DWH updated.")


# =============================================================================
# Option 3 -- Full pipeline: generate + ETL
# =============================================================================

def option_full_pipeline() -> None:
    """Delete database, regenerate Business DB, then run the full ETL pipeline."""
    db_path = ROOT / "data" / "furniture.db"
    if db_path.exists():
        answer = input(
            f"\n  Database exists ({db_path.name}). Full pipeline will DELETE everything.\n"
            "  Continue? (yes/no): "
        ).strip().lower()
        if answer != "yes":
            print("  Aborted.")
            return
        db_path.unlink()
        print()

    print("  Step 1/2 -- Generating Business DB data ...")
    gen_main()

    print("\n  Step 2/2 -- Running ETL pipeline ...")
    etl_main()
    print("\n  Full pipeline complete.")


# =============================================================================
# Option 4 -- Execute analytical query
# =============================================================================

def print_question_menu() -> None:
    print("\n  Available analytical questions:")
    print("  " + "-" * 62)
    for key, (description, _) in QUESTIONS.items():
        first_line = description.split("\n")[0]
        print(f"  {key:5s}  {first_line}")
    print("  " + "-" * 62)
    print("  (Enter question ID, e.g. Q1, Q2a, Q7)")


def option_query() -> None:
    db_path = ROOT / "data" / "furniture.db"
    if not db_path.exists():
        print("\n  Database not found. Run option 1 or 3 first.")
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
# Option 5 -- Generate demo incremental data
# =============================================================================

def option_delta() -> None:
    """Add 2 suppliers, 2 products, 10 customers, 100 orders, and change 5 addresses."""
    db_path = ROOT / "data" / "furniture.db"
    if not db_path.exists():
        print("\n  Business DB not found. Run option 1 or 3 first to generate source data.")
        return
    print("  Generating incremental demo data ...")
    delta_main()
    print("\n  Delta applied. Re-run option 2 (ETL) to load changes into the DWH.")


# =============================================================================
# Main loop
# =============================================================================

BANNER = r"""
  +==============================================================+
  |     Online Furniture Data Warehouse - CLI                    |
  +==============================================================+
"""

MAIN_MENU = """
  Main menu:
    1  Generate Business DB           (Faker -- source tables only)
    2  Run ETL pipeline               (DWH only -- requires Business DB)
    3  Full pipeline: generate + ETL  (start from scratch)
    4  Execute an analytical query
    5  Generate demo delta            (new data + SCD 2 address changes)
    q  Quit
"""


def main() -> None:
    print(BANNER)
    while True:
        print(MAIN_MENU)
        choice = input("  Enter option: ").strip().lower()
        if choice == "1":
            option_generate()
        elif choice == "2":
            option_etl()
        elif choice == "3":
            option_full_pipeline()
        elif choice == "4":
            option_query()
        elif choice == "5":
            option_delta()
        elif choice in ("q", "quit", "exit"):
            print("\n  Goodbye.\n")
            break
        else:
            print("  Invalid option. Please enter 1, 2, 3, 4, or q.")


if __name__ == "__main__":
    main()
