"""
Run_All_ETL.py — ETL Orchestrator
Runs the complete ETL pipeline in dependency order:
  1. Extract   → RAW_ staging tables
  2. DimDate   → dim_date
  3. DimSupplier → dim_supplier
  4. DimProduct  → dim_product (SCD1)
  5. DimCustomer → dim_customer (SCD2)
  6. FactSales   → fact_sales

Usage:
    python python/etl/run_all_etl.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect

from etl_extract      import run_etl_extract
from etl_dim_date     import run_etl_dim_date
from etl_dim_supplier import run_etl_dim_supplier
from etl_dim_product  import run_etl_dim_product
from etl_dim_customer import run_etl_dim_customer
from etl_fact_sales   import run_etl_fact_sales


def run_all_etl() -> None:
    print("Running ETL pipeline …")
    run_etl_extract()
    run_etl_dim_date()
    run_etl_dim_supplier()
    run_etl_dim_product()
    run_etl_dim_customer()
    run_etl_fact_sales()

    # Row count summary
    conn = connect()
    try:
        print("\nRow counts:")
        for tbl in ["dim_date", "dim_customer", "dim_product", "dim_supplier", "fact_sales"]:
            n = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"  {tbl:25s} {n:>8,}")
    finally:
        conn.close()
    print("\nETL complete.")


if __name__ == "__main__":
    run_all_etl()
