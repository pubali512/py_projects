"""
ETL pipeline: Business DB → DWH (star schema)

Steps:
  1. Extract  — copy Business DB tables to RAW_ staging tables
  2. Transform — enrich and compute measures in FULL_ staging tables
  3. Load      — upsert dimensions, append to fact_sales

Staging table naming convention:
  RAW_BusinessDB_<Object>
  FULL_BusinessDB_DWH_<Object>

Run:
    python python/02_etl.py
"""

import pathlib
import sys
from datetime import date, timedelta
from calendar import isleap

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect, PLACEHOLDER

ROOT    = pathlib.Path(__file__).parent.parent.parent
DWH_DDL = ROOT / "sql" / "02_create_dwh.sql"


# =============================================================================
# Helpers
# =============================================================================

def _iso_to_int(iso_date: str) -> int:
    """Convert ISO date string 'YYYY-MM-DD' to integer surrogate key YYYYMMDD."""
    return int(iso_date.replace("-", ""))


def _calendar_week(d: date) -> int:
    return d.isocalendar()[1]


def _weekday_name(wd: int) -> str:
    return ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
            "Freitag", "Samstag", "Sonntag"][wd]


def _month_name(m: int) -> str:
    return ["Januar", "Februar", "März", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Dezember"][m - 1]


# =============================================================================
# Step 0 — Apply DWH DDL (idempotent)
# =============================================================================

def apply_dwh_ddl(conn) -> None:
    ddl = DWH_DDL.read_text(encoding="utf-8")
    conn.executescript(ddl)
    conn.commit()


# =============================================================================
# Step 1 — Extract: Business DB → RAW staging tables
# =============================================================================

def extract(conn) -> None:
    print("  [1] Extract → RAW staging tables")
    tables = {
        "customer":     "RAW_BusinessDB_Customer",
        "order_header": "RAW_BusinessDB_OrderHeader",
        "order_line":   "RAW_BusinessDB_OrderLine",
        "product":      "RAW_BusinessDB_Product",
        "category":     "RAW_BusinessDB_Category",
        "supplier":     "RAW_BusinessDB_Supplier",
    }
    for src, raw in tables.items():
        conn.execute(f"DELETE FROM {raw}")
        conn.execute(f"INSERT INTO {raw} SELECT * FROM {src}")
    conn.commit()


# =============================================================================
# Step 2 — Transform: RAW → FULL staging tables
# =============================================================================

def transform(conn) -> None:
    print("  [2] Transform → FULL staging tables")

    # ── FULL_BusinessDB_DWH_Customer ─────────────────────────────────────────
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
            substr(postal_code, 1, 1) AS plz_region,
            substr(postal_code, 1, 2) AS plz_zone,
            city,
            federal_state,
            customer_since
        FROM RAW_BusinessDB_Customer
    """)

    # ── FULL_BusinessDB_DWH_Product (flatten category hierarchy) ────────────
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
        FROM RAW_BusinessDB_Product p
        JOIN RAW_BusinessDB_Category c   ON p.category_id = c.category_id
        LEFT JOIN RAW_BusinessDB_Category top ON c.parent_category_id = top.category_id
    """)

    # ── FULL_BusinessDB_DWH_Sales (compute measures) ─────────────────────────
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
            ROUND(ol.quantity * ol.unit_price, 2)                            AS gross_amount,
            ROUND(ol.quantity * ol.unit_price * ol.discount, 2)              AS discount_amount,
            ROUND(ol.quantity * ol.unit_price * (1.0 - ol.discount), 2)      AS net_amount
        FROM RAW_BusinessDB_OrderLine ol
        JOIN RAW_BusinessDB_OrderHeader oh ON ol.order_id    = oh.order_id
        JOIN RAW_BusinessDB_Product     p  ON ol.product_id  = p.product_id
    """)
    conn.commit()


# =============================================================================
# Step 3a — Load: dim_date
# =============================================================================

def load_dim_date(conn) -> None:
    print("  [3a] Load → dim_date")
    existing = {row[0] for row in conn.execute("SELECT date_sk FROM dim_date")}

    dates_needed = {
        row[0]
        for row in conn.execute("SELECT DISTINCT order_date FROM FULL_BusinessDB_DWH_Sales")
    }

    rows = []
    for ds in dates_needed:
        sk = _iso_to_int(ds)
        if sk in existing:
            continue
        d = date.fromisoformat(ds)
        rows.append((
            sk,
            ds,
            d.day,
            d.month,
            _month_name(d.month),
            (d.month - 1) // 3 + 1,
            d.year,
            d.weekday(),
            _weekday_name(d.weekday()),
            _calendar_week(d),
        ))

    if rows:
        conn.executemany(
            f"INSERT INTO dim_date VALUES ({','.join([PLACEHOLDER]*10)})",
            rows,
        )
    conn.commit()
    print(f"     {len(rows)} new date rows")


# =============================================================================
# Step 3b — Load: dim_supplier (SCD 0 — insert new, ignore existing)
# =============================================================================

def load_dim_supplier(conn) -> None:
    print("  [3b] Load → dim_supplier")
    existing = {row[0] for row in conn.execute("SELECT supplier_id FROM dim_supplier")}

    rows = conn.execute("SELECT * FROM RAW_BusinessDB_Supplier").fetchall()
    new_rows = [r for r in rows if r["supplier_id"] not in existing]
    if new_rows:
        conn.executemany(
            f"INSERT INTO dim_supplier (supplier_id, supplier_name, city, country) "
            f"VALUES ({','.join([PLACEHOLDER]*4)})",
            [(r["supplier_id"], r["supplier_name"], r["city"], r["country"])
             for r in new_rows],
        )
    conn.commit()
    print(f"     {len(new_rows)} new supplier rows")


# =============================================================================
# Step 3c — Load: dim_product (SCD 1 — overwrite changed attributes)
# =============================================================================

def load_dim_product(conn) -> None:
    print("  [3c] Load → dim_product")
    existing = {
        row[0]: row
        for row in conn.execute(
            "SELECT product_id, product_name, colour, material, list_price, "
            "category_name, top_category_name FROM dim_product"
        )
    }

    inserted = updated = 0
    for r in conn.execute("SELECT * FROM FULL_BusinessDB_DWH_Product").fetchall():
        pid = r["product_id"]
        if pid not in existing:
            conn.execute(
                f"INSERT INTO dim_product "
                f"(product_id, product_name, colour, material, list_price, category_name, top_category_name) "
                f"VALUES ({','.join([PLACEHOLDER]*7)})",
                (pid, r["product_name"], r["colour"], r["material"],
                 r["list_price"], r["category_name"], r["top_category_name"]),
            )
            inserted += 1
        else:
            ex = existing[pid]
            if (ex[1], ex[2], ex[3], ex[4], ex[5], ex[6]) != (
                    r["product_name"], r["colour"], r["material"],
                    r["list_price"], r["category_name"], r["top_category_name"]):
                conn.execute(
                    f"UPDATE dim_product SET product_name={PLACEHOLDER}, colour={PLACEHOLDER}, "
                    f"material={PLACEHOLDER}, list_price={PLACEHOLDER}, "
                    f"category_name={PLACEHOLDER}, top_category_name={PLACEHOLDER} "
                    f"WHERE product_id={PLACEHOLDER}",
                    (r["product_name"], r["colour"], r["material"],
                     r["list_price"], r["category_name"], r["top_category_name"], pid),
                )
                updated += 1
    conn.commit()
    print(f"     {inserted} inserted, {updated} updated (SCD1)")


# =============================================================================
# Step 3d — Load: dim_customer (SCD 2 — expire old row, insert new on address change)
# =============================================================================

def load_dim_customer(conn) -> None:
    print("  [3d] Load → dim_customer (SCD2)")
    etl_date = date.today().isoformat()
    inserted = expired = 0

    for r in conn.execute("SELECT * FROM FULL_BusinessDB_DWH_Customer").fetchall():
        cid = r["customer_id"]
        current = conn.execute(
            "SELECT customer_sk, postal_code, street_address FROM dim_customer "
            "WHERE customer_id=? AND is_current=1",
            (cid,),
        ).fetchone()

        if current is None:
            # New customer — insert first row
            conn.execute(
                f"INSERT INTO dim_customer "
                f"(customer_id, first_name, last_name, email, street_address, postal_code, "
                f"plz_region, plz_zone, city, federal_state, valid_from, valid_to, is_current) "
                f"VALUES ({','.join([PLACEHOLDER]*13)})",
                (cid, r["first_name"], r["last_name"], r["email"],
                 r["street_address"], r["postal_code"],
                 r["plz_region"], r["plz_zone"], r["city"], r["federal_state"],
                 r["customer_since"], None, 1),
            )
            inserted += 1
        elif current["postal_code"] != r["postal_code"] or \
                current["street_address"] != r["street_address"]:
            # Address changed → expire current row, insert new
            conn.execute(
                f"UPDATE dim_customer SET valid_to={PLACEHOLDER}, is_current=0 "
                f"WHERE customer_sk={PLACEHOLDER}",
                (etl_date, current["customer_sk"]),
            )
            conn.execute(
                f"INSERT INTO dim_customer "
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
    print(f"     {inserted} new, {expired} expired (SCD2)")


# =============================================================================
# Step 3e — Load: fact_sales
# =============================================================================

def load_fact_sales(conn) -> None:
    print("  [3e] Load → fact_sales")

    # Build lookup maps (natural key → surrogate key)
    product_map = {
        r[0]: r[1]
        for r in conn.execute("SELECT product_id, product_sk FROM dim_product")
    }
    supplier_map = {
        r[0]: r[1]
        for r in conn.execute("SELECT supplier_id, supplier_sk FROM dim_supplier")
    }
    # customer_map: customer_id → customer_sk (current row only)
    customer_map = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT customer_id, customer_sk FROM dim_customer WHERE is_current=1"
        )
    }

    # Already-loaded order lines (avoid duplicates on re-run)
    loaded_order_ids = {
        r[0] for r in conn.execute("SELECT DISTINCT order_id FROM fact_sales")
    }

    batch = []
    for r in conn.execute("SELECT * FROM FULL_BusinessDB_DWH_Sales").fetchall():
        if r["order_id"] in loaded_order_ids:
            continue
        date_sk     = _iso_to_int(r["order_date"])
        customer_sk = customer_map.get(r["customer_id"])
        product_sk  = product_map.get(r["product_id"])
        supplier_sk = supplier_map.get(r["supplier_id"])
        if not all([customer_sk, product_sk, supplier_sk]):
            continue  # skip orphan rows (should not occur with valid data)
        batch.append((
            date_sk, customer_sk, product_sk, supplier_sk,
            r["order_id"], r["quantity"],
            r["gross_amount"], r["discount_amount"], r["net_amount"],
            r["shipping_cost"],
        ))

    if batch:
        conn.executemany(
            f"INSERT INTO fact_sales "
            f"(date_sk, customer_sk, product_sk, supplier_sk, order_id, quantity, "
            f"gross_amount, discount_amount, net_amount, shipping_cost) "
            f"VALUES ({','.join([PLACEHOLDER]*10)})",
            batch,
        )
    conn.commit()
    print(f"     {len(batch)} fact rows inserted")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    conn = connect()
    print("Applying DWH DDL …")
    apply_dwh_ddl(conn)

    print("Running ETL pipeline …")
    extract(conn)
    transform(conn)
    load_dim_date(conn)
    load_dim_supplier(conn)
    load_dim_product(conn)
    load_dim_customer(conn)
    load_fact_sales(conn)

    # Validation summary
    print("\nRow counts:")
    for tbl in ["dim_date", "dim_customer", "dim_product", "dim_supplier", "fact_sales"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  {tbl:25s} {n:>8,}")
    conn.close()
    print("\nETL complete.")


if __name__ == "__main__":
    main()
