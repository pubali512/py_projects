"""
ETL_FactSales.py — Fact table: fact_sales
Reads order lines from RAW staging tables, computes monetary measures,
resolves surrogate keys, and appends new rows to fact_sales.
Grain: one row per order line.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect, PLACEHOLDER


def extract_fact_sales(conn) -> list:
    """Join RAW order lines, headers, and products to get all measure source data."""
    return conn.execute("""
        SELECT ol.order_line_id,
               ol.order_id,
               oh.order_date,
               oh.customer_id,
               ol.product_id,
               p.supplier_id,
               ol.quantity,
               ol.unit_price,
               ol.discount,
               oh.shipping_cost
        FROM RAW_BusinessDB_OrderLine   ol
        JOIN RAW_BusinessDB_OrderHeader oh ON ol.order_id   = oh.order_id
        JOIN RAW_BusinessDB_Product     p  ON ol.product_id = p.product_id
    """).fetchall()


def transform_fact_sales(
    raw_rows: list,
    product_map: dict,
    supplier_map: dict,
    customer_map: dict,
    loaded_order_ids: set,
) -> list[tuple]:
    """Resolve surrogate keys and compute gross/discount/net amounts.
    Skips rows for orders already present in fact_sales (idempotent re-run).
    """
    rows = []
    for r in raw_rows:
        if r["order_id"] in loaded_order_ids:
            continue
        date_sk     = int(r["order_date"].replace("-", ""))
        customer_sk = customer_map.get(r["customer_id"])
        product_sk  = product_map.get(r["product_id"])
        supplier_sk = supplier_map.get(r["supplier_id"])
        if not all([customer_sk, product_sk, supplier_sk]):
            continue  # orphan row — should not occur with valid data
        gross    = round(r["quantity"] * r["unit_price"], 2)
        discount = round(gross * r["discount"], 2)
        net      = round(gross - discount, 2)
        rows.append((
            date_sk, customer_sk, product_sk, supplier_sk,
            r["order_id"], r["quantity"],
            gross, discount, net,
            r["shipping_cost"],
        ))
    return rows


def load_fact_sales(conn, rows: list[tuple]) -> int:
    """Append fact rows to fact_sales; returns count of inserted rows."""
    if rows:
        conn.executemany(
            f"INSERT INTO fact_sales "
            f"(date_sk, customer_sk, product_sk, supplier_sk, order_id, quantity, "
            f"gross_amount, discount_amount, net_amount, shipping_cost) "
            f"VALUES ({','.join([PLACEHOLDER]*10)})",
            rows,
        )
        conn.commit()
    return len(rows)


def run_etl_fact_sales() -> None:
    conn = connect()
    try:
        product_map  = {r[0]: r[1] for r in conn.execute("SELECT product_id,  product_sk  FROM dim_product")}
        supplier_map = {r[0]: r[1] for r in conn.execute("SELECT supplier_id, supplier_sk FROM dim_supplier")}
        customer_map = {r[0]: r[1] for r in conn.execute(
            "SELECT customer_id, customer_sk FROM dim_customer WHERE is_current=1"
        )}
        loaded_order_ids = {r[0] for r in conn.execute("SELECT DISTINCT order_id FROM fact_sales")}

        raw  = extract_fact_sales(conn)
        rows = transform_fact_sales(raw, product_map, supplier_map, customer_map, loaded_order_ids)
        n    = load_fact_sales(conn, rows)
        print(f"  [FactSales]   {n:>6,} new rows inserted")
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl_fact_sales()
