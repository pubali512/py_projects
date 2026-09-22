"""
ETL_DimSupplier.py -- Dimension: dim_supplier  (SCD Type 0)
Reads suppliers from RAW_BusinessDB_Supplier and inserts new rows.
Existing suppliers are never overwritten (SCD 0).
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect, PLACEHOLDER


def extract_dim_supplier(conn) -> list:
    """Return all supplier rows from the RAW staging table."""
    return conn.execute("SELECT * FROM RAW_BusinessDB_Supplier").fetchall()


def transform_dim_supplier(raw_rows: list, existing_ids: set) -> list[tuple]:
    """Filter out suppliers already present in dim_supplier."""
    return [
        (r["supplier_id"], r["supplier_name"], r["city"], r["country"])
        for r in raw_rows
        if r["supplier_id"] not in existing_ids
    ]


def load_dim_supplier(conn, rows: list[tuple]) -> int:
    """Insert new supplier rows into dim_supplier; returns count of inserted rows."""
    if rows:
        conn.executemany(
            f"INSERT INTO dim_supplier (supplier_id, supplier_name, city, country) "
            f"VALUES ({','.join([PLACEHOLDER] * 4)})",
            rows,
        )
        conn.commit()
    return len(rows)


def run_etl_dim_supplier() -> None:
    conn = connect()
    try:
        existing_ids = {r[0] for r in conn.execute("SELECT supplier_id FROM dim_supplier")}
        raw = extract_dim_supplier(conn)
        rows = transform_dim_supplier(raw, existing_ids)
        n = load_dim_supplier(conn, rows)
        print(f"  [DimSupplier] {n:>6,} new rows inserted")
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl_dim_supplier()
