"""
Online Furniture Data Warehouse — Command-Line Front-End

Usage:
    python python/run.py

Options presented interactively:
    1. Load and transform the database (generate data → run ETL)
    2. Execute an analytical query (choose from Q1–Q6, Q-S1, Q-S2)
"""

import pathlib
import sqlite3
import sys
import textwrap

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from db import connect

ROOT = pathlib.Path(__file__).parent.parent

# =============================================================================
# Analytical question catalogue
# =============================================================================

QUESTIONS: dict[str, tuple[str, str]] = {
    "Q1": (
        "Revenue and discount by category over time\n"
        "  How does net revenue develop per top-level product category and quarter,\n"
        "  and which category carries the highest discount share?",
        """
        SELECT dp.top_category_name, dd.year, dd.quarter,
               ROUND(SUM(fs.net_amount),2)    AS net_revenue,
               ROUND(SUM(fs.gross_amount),2)  AS gross_revenue,
               ROUND(SUM(fs.discount_amount),2) AS total_discount,
               ROUND(100.0*SUM(fs.discount_amount)/NULLIF(SUM(fs.gross_amount),0),2)
                                              AS discount_share_pct
        FROM fact_sales fs
        JOIN dim_date    dd ON fs.date_sk    = dd.date_sk
        JOIN dim_product dp ON fs.product_sk = dp.product_sk
        GROUP BY dp.top_category_name, dd.year, dd.quarter
        ORDER BY dd.year, dd.quarter, net_revenue DESC
        """,
    ),
    "Q2a": (
        "Average order value by PLZ region (Part A)\n"
        "  Which postal code regions generate the highest average order value?\n"
        "  (order value = sum of net line amounts + shipping cost)",
        """
        WITH order_totals AS (
            SELECT dc.plz_region, fs.order_id,
                   SUM(fs.net_amount) + MAX(fs.shipping_cost) AS order_value
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_sk = dc.customer_sk
            WHERE dc.is_current = 1
            GROUP BY dc.plz_region, fs.order_id
        )
        SELECT plz_region,
               COUNT(DISTINCT order_id)   AS order_count,
               ROUND(AVG(order_value),2)  AS avg_order_value,
               ROUND(SUM(order_value),2)  AS total_revenue
        FROM order_totals
        GROUP BY plz_region
        ORDER BY avg_order_value DESC
        """,
    ),
    "Q2b": (
        "Product category mix by PLZ region (Part B)\n"
        "  Does the product category mix differ between postal code regions?",
        """
        SELECT dc.plz_region, dp.top_category_name,
               ROUND(SUM(fs.net_amount),2) AS net_revenue,
               ROUND(100.0*SUM(fs.net_amount)
                   /SUM(SUM(fs.net_amount)) OVER (PARTITION BY dc.plz_region),1)
                                           AS category_share_pct
        FROM fact_sales fs
        JOIN dim_customer dc ON fs.customer_sk = dc.customer_sk
        JOIN dim_product  dp ON fs.product_sk  = dp.product_sk
        WHERE dc.is_current = 1
        GROUP BY dc.plz_region, dp.top_category_name
        ORDER BY dc.plz_region, net_revenue DESC
        """,
    ),
    "Q3a": (
        "Peak order volume by weekday\n"
        "  Which weekdays see the highest order volume across the two-year period?",
        """
        SELECT dd.weekday_name, dd.weekday,
               COUNT(DISTINCT fs.order_id) AS order_count,
               SUM(fs.quantity)            AS total_units,
               ROUND(SUM(fs.net_amount),2) AS net_revenue
        FROM fact_sales fs
        JOIN dim_date dd ON fs.date_sk = dd.date_sk
        GROUP BY dd.weekday, dd.weekday_name
        ORDER BY order_count DESC
        """,
    ),
    "Q3b": (
        "Peak order volume by calendar week (Top 10)\n"
        "  Which calendar weeks see the highest order volume?",
        """
        SELECT dd.year, dd.calendar_week,
               COUNT(DISTINCT fs.order_id) AS order_count,
               ROUND(SUM(fs.net_amount),2) AS net_revenue
        FROM fact_sales fs
        JOIN dim_date dd ON fs.date_sk = dd.date_sk
        GROUP BY dd.year, dd.calendar_week
        ORDER BY order_count DESC
        LIMIT 10
        """,
    ),
    "Q4": (
        "Discount effectiveness\n"
        "  Does a higher discount rate correlate with higher quantity sold\n"
        "  or net revenue per order line?",
        """
        SELECT
            CASE
                WHEN discount_amount = 0 THEN '0%  (no discount)'
                WHEN CAST(discount_amount AS REAL)/gross_amount < 0.05 THEN '1-5%'
                WHEN CAST(discount_amount AS REAL)/gross_amount < 0.10 THEN '5-10%'
                WHEN CAST(discount_amount AS REAL)/gross_amount < 0.15 THEN '10-15%'
                WHEN CAST(discount_amount AS REAL)/gross_amount < 0.20 THEN '15-20%'
                ELSE '20%+'
            END                         AS discount_bucket,
            COUNT(*)                    AS order_line_count,
            ROUND(AVG(quantity),2)      AS avg_quantity,
            ROUND(AVG(net_amount),2)    AS avg_net_amount_per_line,
            ROUND(SUM(net_amount),2)    AS total_net_revenue
        FROM fact_sales
        GROUP BY discount_bucket
        ORDER BY MIN(CAST(discount_amount AS REAL)/gross_amount)
        """,
    ),
    "Q5": (
        "Revenue and discount share by price segment\n"
        "  How does revenue and discount compare across Budget (<€200) /\n"
        "  Mid-range (€200–€799) / Premium (≥€800) product segments?",
        """
        SELECT
            CASE
                WHEN dp.list_price < 200.0 THEN 'Budget (< EUR 200)'
                WHEN dp.list_price < 800.0 THEN 'Mid-range (EUR 200-799)'
                ELSE                            'Premium (>= EUR 800)'
            END                         AS price_segment,
            COUNT(*)                    AS order_line_count,
            SUM(fs.quantity)            AS total_units_sold,
            ROUND(SUM(fs.net_amount),2) AS net_revenue,
            ROUND(100.0*SUM(fs.discount_amount)/NULLIF(SUM(fs.gross_amount),0),2)
                                        AS discount_share_pct
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_sk = dp.product_sk
        GROUP BY price_segment
        ORDER BY MIN(dp.list_price)
        """,
    ),
    "Q6": (
        "Federal state revenue growth: Year 1 (2024) vs Year 2 (2025)\n"
        "  Which federal states show the strongest revenue growth?",
        """
        WITH yearly AS (
            SELECT dc.federal_state, dd.year, SUM(fs.net_amount) AS net_revenue
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_sk = dc.customer_sk
            JOIN dim_date     dd ON fs.date_sk     = dd.date_sk
            WHERE dc.is_current = 1
            GROUP BY dc.federal_state, dd.year
        )
        SELECT y1.federal_state,
               ROUND(y1.net_revenue,2) AS revenue_2024,
               ROUND(y2.net_revenue,2) AS revenue_2025,
               ROUND(100.0*(y2.net_revenue-y1.net_revenue)/NULLIF(y1.net_revenue,0),2)
                                       AS growth_pct
        FROM yearly y1
        JOIN yearly y2
            ON  y1.federal_state = y2.federal_state
            AND y1.year = 2024
            AND y2.year = 2025
        ORDER BY growth_pct DESC
        """,
    ),
    "Q-S1": (
        "Supplier revenue by quarter\n"
        "  Which suppliers generate the most net revenue per quarter,\n"
        "  and how has their share shifted over the two-year period?",
        """
        SELECT ds.supplier_name, dd.year, dd.quarter,
               ROUND(SUM(fs.net_amount),2) AS net_revenue,
               COUNT(*)                    AS order_line_count,
               ROUND(100.0*SUM(fs.net_amount)
                   /SUM(SUM(fs.net_amount)) OVER (PARTITION BY dd.year, dd.quarter),2)
                                           AS revenue_share_pct
        FROM fact_sales fs
        JOIN dim_supplier ds ON fs.supplier_sk = ds.supplier_sk
        JOIN dim_date     dd ON fs.date_sk     = dd.date_sk
        GROUP BY ds.supplier_name, dd.year, dd.quarter
        ORDER BY dd.year, dd.quarter, net_revenue DESC
        """,
    ),
    "Q-S2": (
        "Supplier discount behaviour vs. order volume\n"
        "  Which suppliers' products carry the highest average discount rate,\n"
        "  and does that correlate with order volume?",
        """
        SELECT ds.supplier_name,
               COUNT(*)                    AS order_line_count,
               SUM(fs.quantity)            AS total_units_sold,
               ROUND(SUM(fs.net_amount),2) AS total_net_revenue,
               ROUND(100.0*SUM(fs.discount_amount)/NULLIF(SUM(fs.gross_amount),0),2)
                                           AS avg_discount_pct,
               ROUND(SUM(fs.net_amount)/NULLIF(COUNT(*),0),2)
                                           AS avg_revenue_per_line
        FROM fact_sales fs
        JOIN dim_supplier ds ON fs.supplier_sk = ds.supplier_sk
        GROUP BY ds.supplier_name
        ORDER BY avg_discount_pct DESC
        """,
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
# Option 1 — Load and transform
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

    print("  Step 1/2 — Generating Business DB data …")
    import importlib
    gen = importlib.import_module("data_gen.generate_data")
    importlib.reload(gen)
    gen.main()

    print("\n  Step 2/2 — Running ETL pipeline …")
    etl_mod = importlib.import_module("etl.etl")
    importlib.reload(etl_mod)
    etl_mod.main()

    print("\n  Database loaded and transformed successfully.")


# =============================================================================
# Option 2 — Execute analytical query
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

    description, sql = QUESTIONS[choice]
    print(f"\n{'='*66}")
    print(f"  {choice} — {description}")
    print(f"{'='*66}\n")

    conn = connect()
    try:
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
  ║     Online Furniture Data Warehouse — CLI                    ║
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
