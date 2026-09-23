"""
ETL_DimCustomer.py -- Dimension: DIM_Customer  (SCD Type 2)
Reads customers from RAW_BusinessDB_Customer, derives PLZ region/zone,
and applies SCD Type 2 logic:
  - New customer   -> INSERT (ValidFrom = CustomerSince, ValidTo = NULL, IsCurrent = 1)
  - Address change -> expire old row (ValidTo = today), INSERT new row
  - No change      -> skip
"""

import pathlib
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect, PLACEHOLDER


def extract_dim_customer(conn) -> list:
    """Return all customer rows from the FULL_ staging table."""
    return conn.execute("SELECT * FROM FULL_BusinessDB_DWH_Customer").fetchall()


def transform_dim_customer(full_rows: list) -> list[dict]:
    """Pass through enriched rows from FULL_ staging (PlzRegion/PlzZone already derived)."""
    return [
        {
            "CustomerId":    r["CustomerId"],
            "FirstName":     r["FirstName"],
            "LastName":      r["LastName"],
            "Email":          r["Email"],
            "StreetAddress": r["StreetAddress"],
            "PostalCode":    r["PostalCode"],
            "PlzRegion":     r["PlzRegion"],
            "PlzZone":       r["PlzZone"],
            "City":           r["City"],
            "FederalState":  r["FederalState"],
            "CustomerSince": r["CustomerSince"],
        }
        for r in full_rows
    ]


def load_dim_customer(conn, rows: list[dict]) -> tuple[int, int]:
    """Apply SCD2 logic.  Returns (inserted_new, expired_and_reinserted)."""
    etl_date = date.today().isoformat()
    inserted = expired = 0

    for r in rows:
        cid = r["CustomerId"]
        current = conn.execute(
            "SELECT CustomerSk, PostalCode, StreetAddress FROM DIM_Customer "
            "WHERE CustomerId=? AND IsCurrent=1",
            (cid,),
        ).fetchone()

        if current is None:
            conn.execute(
                f"INSERT INTO DIM_Customer "
                f"(CustomerId, FirstName, LastName, Email, StreetAddress, PostalCode, "
                f"PlzRegion, PlzZone, City, FederalState, ValidFrom, ValidTo, IsCurrent) "
                f"VALUES ({','.join([PLACEHOLDER]*13)})",
                (cid, r["FirstName"], r["LastName"], r["Email"],
                 r["StreetAddress"], r["PostalCode"],
                 r["PlzRegion"], r["PlzZone"], r["City"], r["FederalState"],
                 r["CustomerSince"], None, 1),
            )
            inserted += 1
        elif (current["PostalCode"] != r["PostalCode"] or
              current["StreetAddress"] != r["StreetAddress"]):
            conn.execute(
                f"UPDATE DIM_Customer SET ValidTo={PLACEHOLDER}, IsCurrent=0 "
                f"WHERE CustomerSk={PLACEHOLDER}",
                (etl_date, current["CustomerSk"]),
            )
            conn.execute(
                f"INSERT INTO DIM_Customer "
                f"(CustomerId, FirstName, LastName, Email, StreetAddress, PostalCode, "
                f"PlzRegion, PlzZone, City, FederalState, ValidFrom, ValidTo, IsCurrent) "
                f"VALUES ({','.join([PLACEHOLDER]*13)})",
                (cid, r["FirstName"], r["LastName"], r["Email"],
                 r["StreetAddress"], r["PostalCode"],
                 r["PlzRegion"], r["PlzZone"], r["City"], r["FederalState"],
                 etl_date, None, 1),
            )
            expired += 1

    conn.commit()
    return inserted, expired


def run_etl_dim_customer() -> None:
    conn = connect()
    try:
        raw = extract_dim_customer(conn)
        rows = transform_dim_customer(raw)
        inserted, expired = load_dim_customer(conn, rows)
        print(f"  [DimCustomer] {inserted:>6,} new, {expired:>4,} expired (SCD2)")
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl_dim_customer()
