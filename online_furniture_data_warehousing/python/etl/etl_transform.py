"""
ETL_Transform.py — Step 2: Transform
Reads from RAW_ staging tables, applies enrichment and measure computation,
and writes results to FULL_ staging tables.

FULL_ tables serve as the cleansed/enriched staging layer between
the raw extract (RAW_) and the DWH target (dim_* / fact_*).
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect


def transform_full_customer(conn) -> int:
    """Derive plz_region and plz_zone from postal_code; write to FULL_BusinessDB_DWH_Customer."""
    conn.execute("DELETE FROM FULL_BusinessDB_DWH_Customer")
    conn.execute("""
        INSERT INTO FULL_BusinessDB_DWH_Customer
        SELECT
            customer_id,
            first_name,
            last_name,
            email,
            street_address,
            postal_code,
            substr(postal_code, 1, 1)  AS plz_region,
            substr(postal_code, 1, 2)  AS plz_zone,
            city,
            federal_state,
            customer_since
        FROM RAW_BusinessDB_Customer
    """)
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM FULL_BusinessDB_DWH_Customer").fetchone()[0]


def transform_full_product(conn) -> int:
    """Flatten the category hierarchy (sub → top); write to FULL_BusinessDB_DWH_Product."""
    conn.execute("DELETE FROM FULL_BusinessDB_DWH_Product")
    conn.execute("""
        INSERT INTO FULL_BusinessDB_DWH_Product
        SELECT
            p.product_id,
            p.product_name,
            p.colour,
            p.material,
            p.list_price,
            c.category_name,
            COALESCE(top.category_name, c.category_name) AS top_category_name,
            p.supplier_id
        FROM RAW_BusinessDB_Product      p
        JOIN RAW_BusinessDB_Category     c   ON p.category_id      = c.category_id
        LEFT JOIN RAW_BusinessDB_Category top ON c.parent_category_id = top.category_id
    """)
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM FULL_BusinessDB_DWH_Product").fetchone()[0]


def transform_full_sales(conn) -> int:
    """Compute gross / discount / net amounts; write to FULL_BusinessDB_DWH_Sales."""
    conn.execute("DELETE FROM FULL_BusinessDB_DWH_Sales")
    conn.execute("""
        INSERT INTO FULL_BusinessDB_DWH_Sales
        SELECT
            ol.order_line_id,
            ol.order_id,
            oh.order_date,
            oh.customer_id,
            ol.product_id,
            p.supplier_id,
            ol.quantity,
            ol.unit_price,
            ol.discount,
            oh.shipping_cost,
            ROUND(ol.quantity * ol.unit_price, 2)                        AS gross_amount,
            ROUND(ol.quantity * ol.unit_price * ol.discount, 2)          AS discount_amount,
            ROUND(ol.quantity * ol.unit_price * (1.0 - ol.discount), 2)  AS net_amount
        FROM RAW_BusinessDB_OrderLine   ol
        JOIN RAW_BusinessDB_OrderHeader oh ON ol.order_id   = oh.order_id
        JOIN RAW_BusinessDB_Product     p  ON ol.product_id = p.product_id
    """)
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM FULL_BusinessDB_DWH_Sales").fetchone()[0]


def run_etl_transform() -> None:
    conn = connect()
    try:
        n = transform_full_customer(conn)
        print(f"  [Transform]   FULL_BusinessDB_DWH_Customer  {n:>8,} rows")
        n = transform_full_product(conn)
        print(f"  [Transform]   FULL_BusinessDB_DWH_Product   {n:>8,} rows")
        n = transform_full_sales(conn)
        print(f"  [Transform]   FULL_BusinessDB_DWH_Sales      {n:>8,} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl_transform()
