"""
ETL_FactSales.py -- Fact table: FACT_Sales
Reads order lines from RAW staging tables, computes monetary measures,
resolves surrogate keys, and appends new rows to FACT_Sales.
Grain: one row per order line.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect, PLACEHOLDER


def extract_fact_sales(conn) -> list:
    """Join RAW order lines, headers, and products to get all measure source data."""
    return conn.execute("""
        SELECT ol.OrderLineId,
               ol.OrderId,
               oh.OrderDate,
               oh.CustomerId,
               ol.ProductId,
               p.SupplierId,
               ol.Quantity,
               ol.UnitPrice,
               ol.Discount,
               oh.ShippingCost
        FROM RAW_BusinessDB_OrderLine   ol
        JOIN RAW_BusinessDB_OrderHeader oh ON ol.OrderId   = oh.OrderId
        JOIN RAW_BusinessDB_Product     p  ON ol.ProductId = p.ProductId
    """).fetchall()


def transform_fact_sales(
    raw_rows: list,
    product_map: dict,
    supplier_map: dict,
    customer_map: dict,
    loaded_order_ids: set,
) -> list[tuple]:
    """Resolve surrogate keys and compute gross/Discount/net amounts.
    Skips rows for orders already present in FACT_Sales (idempotent re-run).
    """
    rows = []
    for r in raw_rows:
        if r["OrderId"] in loaded_order_ids:
            continue
        DateSk     = int(r["OrderDate"].replace("-", ""))
        CustomerSk = customer_map.get(r["CustomerId"])
        ProductSk  = product_map.get(r["ProductId"])
        SupplierSk = supplier_map.get(r["SupplierId"])
        if not all([CustomerSk, ProductSk, SupplierSk]):
            continue  # orphan row -- should not occur with valid data
        gross    = round(r["Quantity"] * r["UnitPrice"], 2)
        Discount = round(gross * r["Discount"], 2)
        net      = round(gross - Discount, 2)
        rows.append((
            DateSk, CustomerSk, ProductSk, SupplierSk,
            r["OrderId"], r["Quantity"],
            gross, Discount, net,
            r["ShippingCost"],
        ))
    return rows


def load_fact_sales(conn, rows: list[tuple]) -> int:
    """Append fact rows to FACT_Sales; returns count of inserted rows."""
    if rows:
        conn.executemany(
            f"INSERT INTO FACT_Sales "
            f"(DateSk, CustomerSk, ProductSk, SupplierSk, OrderId, Quantity, "
            f"GrossAmount, DiscountAmount, NetAmount, ShippingCost) "
            f"VALUES ({','.join([PLACEHOLDER]*10)})",
            rows,
        )
        conn.commit()
    return len(rows)


def run_etl_fact_sales() -> None:
    conn = connect()
    try:
        product_map  = {r[0]: r[1] for r in conn.execute("SELECT ProductId,  ProductSk  FROM DIM_Product")}
        supplier_map = {r[0]: r[1] for r in conn.execute("SELECT SupplierId, SupplierSk FROM DIM_Supplier")}
        customer_map = {r[0]: r[1] for r in conn.execute(
            "SELECT CustomerId, CustomerSk FROM DIM_Customer WHERE IsCurrent=1"
        )}
        loaded_order_ids = {r[0] for r in conn.execute("SELECT DISTINCT OrderId FROM FACT_Sales")}

        raw  = extract_fact_sales(conn)
        rows = transform_fact_sales(raw, product_map, supplier_map, customer_map, loaded_order_ids)
        n    = load_fact_sales(conn, rows)
        print(f"  [FactSales]   {n:>6,} new rows inserted")
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl_fact_sales()
