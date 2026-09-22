"""
ETL_Extract.py -- Step 1: Extract
Applies the DWH DDL (idempotent) and copies all Business DB tables into
the RAW_ staging tables for downstream dimension and fact ETL modules.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect

ROOT    = pathlib.Path(__file__).parent.parent.parent
DWH_DDL = ROOT / "sql" / "02_create_dwh.sql"

_RAW_MAP = {
    "customer":     "RAW_BusinessDB_Customer",
    "order_header": "RAW_BusinessDB_OrderHeader",
    "order_line":   "RAW_BusinessDB_OrderLine",
    "product":      "RAW_BusinessDB_Product",
    "category":     "RAW_BusinessDB_Category",
    "supplier":     "RAW_BusinessDB_Supplier",
}


def apply_dwh_ddl(conn) -> None:
    """Create DWH tables and staging tables if they do not exist (idempotent)."""
    ddl = DWH_DDL.read_text(encoding="utf-8")
    conn.executescript(ddl)
    conn.commit()


def extract_to_raw(conn) -> None:
    """Copy every Business DB source table into its corresponding RAW_ staging table."""
    for src, raw in _RAW_MAP.items():
        conn.execute(f"DELETE FROM {raw}")
        conn.execute(f"INSERT INTO {raw} SELECT * FROM {src}")
    conn.commit()


def run_etl_extract() -> None:
    conn = connect()
    try:
        print("  [Extract] Applying DWH DDL ...")
        apply_dwh_ddl(conn)
        print("  [Extract] Copying source tables -> RAW_ staging ...")
        extract_to_raw(conn)
        for raw in _RAW_MAP.values():
            n = conn.execute(f"SELECT COUNT(*) FROM {raw}").fetchone()[0]
            print(f"    {raw:35s} {n:>8,} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl_extract()
