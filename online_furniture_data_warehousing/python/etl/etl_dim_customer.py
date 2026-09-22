"""
ETL_DimCustomer.py -- Dimension: DIM_Customer  (SCD Type 2)
Reads customers from RAW_BusinessDB_Customer, derives PLZ region/zone,
and applies SCD Type 2 logic:
  - New customer   -> INSERT (valid_from = customer_since, valid_to = NULL, is_current = 1)
  - Address change -> expire old row (valid_to = today), INSERT new row
  - No change      -> skip
"""

import pathlib
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect, PLACEHOLDER


def extract_dim_customer(conn) -> list:
    """Return all customer rows from the RAW staging table."""
    return conn.execute("SELECT * FROM RAW_BusinessDB_Customer").fetchall()


def transform_dim_customer(raw_rows: list) -> list[dict]:
    """Derive plz_region and plz_zone from postal_code."""
    result = []
    for r in raw_rows:
        plz = r["postal_code"]
        result.append({
            "customer_id":    r["customer_id"],
            "first_name":     r["first_name"],
            "last_name":      r["last_name"],
            "email":          r["email"],
            "street_address": r["street_address"],
            "postal_code":    plz,
            "plz_region":     plz[:1],
            "plz_zone":       plz[:2],
            "city":           r["city"],
            "federal_state":  r["federal_state"],
            "customer_since": r["customer_since"],
        })
    return result


def load_dim_customer(conn, rows: list[dict]) -> tuple[int, int]:
    """Apply SCD2 logic.  Returns (inserted_new, expired_and_reinserted)."""
    etl_date = date.today().isoformat()
    inserted = expired = 0

    for r in rows:
        cid = r["customer_id"]
        current = conn.execute(
            "SELECT customer_sk, postal_code, street_address FROM DIM_Customer "
            "WHERE customer_id=? AND is_current=1",
            (cid,),
        ).fetchone()

        if current is None:
            conn.execute(
                f"INSERT INTO DIM_Customer "
                f"(customer_id, first_name, last_name, email, street_address, postal_code, "
                f"plz_region, plz_zone, city, federal_state, valid_from, valid_to, is_current) "
                f"VALUES ({','.join([PLACEHOLDER]*13)})",
                (cid, r["first_name"], r["last_name"], r["email"],
                 r["street_address"], r["postal_code"],
                 r["plz_region"], r["plz_zone"], r["city"], r["federal_state"],
                 r["customer_since"], None, 1),
            )
            inserted += 1
        elif (current["postal_code"] != r["postal_code"] or
              current["street_address"] != r["street_address"]):
            conn.execute(
                f"UPDATE DIM_Customer SET valid_to={PLACEHOLDER}, is_current=0 "
                f"WHERE customer_sk={PLACEHOLDER}",
                (etl_date, current["customer_sk"]),
            )
            conn.execute(
                f"INSERT INTO DIM_Customer "
                f"(customer_id, first_name, last_name, email, street_address, postal_code, "
                f"plz_region, plz_zone, city, federal_state, valid_from, valid_to, is_current) "
                f"VALUES ({','.join([PLACEHOLDER]*13)})",
                (cid, r["first_name"], r["last_name"], r["email"],
                 r["street_address"], r["postal_code"],
                 r["plz_region"], r["plz_zone"], r["city"], r["federal_state"],
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
