"""
ETL_Transform.py -- Step 2: Transform
Reads SQL transform scripts from sql/transform/, executes them against the
live database to populate the FULL_ staging tables.

FULL_ tables serve as the cleansed/enriched staging layer between
the raw extract (RAW_) and the DWH target (dim_* / fact_*).
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect

ROOT        = pathlib.Path(__file__).parent.parent.parent
TRANSFORM_DIR = ROOT / "sql" / "transform"

_TRANSFORM_FILES = [
    ("FULL_BusinessDB_DWH_Customer", TRANSFORM_DIR / "01_FULL_customer.sql"),
    ("FULL_BusinessDB_DWH_Product",  TRANSFORM_DIR / "02_FULL_product.sql"),
    ("FULL_BusinessDB_DWH_Sales",    TRANSFORM_DIR / "03_FULL_sales.sql"),
]


def run_etl_transform() -> None:
    conn = connect()
    try:
        for table_name, sql_path in _TRANSFORM_FILES:
            sql = sql_path.read_text(encoding="utf-8")
            conn.executescript(sql)
            n = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"  [Transform]   {table_name:35s} {n:>8,} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl_transform()

