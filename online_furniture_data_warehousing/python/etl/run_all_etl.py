"""
Run_All_ETL.py -- ETL Orchestrator
Runs the complete ETL pipeline in dependency order:
  1. Extract   -> RAW_ staging tables
  2. Transform -> FULL_ staging tables (PLZ derivation, category flatten, measures)
  3. DimDate   -> DIM_Date
  4. DimSupplier -> DIM_Supplier
  5. DimProduct  -> DIM_Product (SCD1)
  6. DimCustomer -> DIM_Customer (SCD2)
  7. FactSales   -> FACT_Sales

Usage:
    python python/etl/run_all_etl.py
"""

import pathlib
import sys

_ETL_DIR = str(pathlib.Path(__file__).parent)
_PYTHON_DIR = str(pathlib.Path(__file__).parent.parent)

# Ensure both python/ and python/etl/ are on the path so imports work
# whether this file is run as a script or imported as etl.run_all_etl.
for _p in (_PYTHON_DIR, _ETL_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from db import connect
from etl_extract      import run_etl_extract
from etl_transform    import run_etl_transform
from etl_dim_date     import run_etl_dim_date
from etl_dim_supplier import run_etl_dim_supplier
from etl_dim_product  import run_etl_dim_product
from etl_dim_customer import run_etl_dim_customer
from etl_fact_sales   import run_etl_fact_sales


def run_all_etl() -> None:
    print("Running ETL pipeline ...")
    run_etl_extract()
    run_etl_transform()
    run_etl_dim_date()
    run_etl_dim_supplier()
    run_etl_dim_product()
    run_etl_dim_customer()
    run_etl_fact_sales()

    # Row count summary
    conn = connect()
    try:
        print("\nRow counts:")
        for tbl in ["DIM_Date", "DIM_Customer", "DIM_Product", "DIM_Supplier", "FACT_Sales"]:
            n = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"  {tbl:25s} {n:>8,}")
    finally:
        conn.close()
    print("\nETL complete.")


if __name__ == "__main__":
    run_all_etl()
