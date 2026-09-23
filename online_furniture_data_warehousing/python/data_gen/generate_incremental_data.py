"""
Incremental data generation for demonstration purposes.

Adds a small delta to the existing Business DB to show:
  - SCD 0 (DIM_Supplier): 2 new suppliers -> 2 new DIM rows on next ETL
  - SCD 1 (DIM_Product):  2 new products  -> 2 new DIM rows on next ETL
  - Customer inserts:     10 new customers -> 10 new DIM_Customer rows
  - New orders:           100 orders       -> new FACT_Sales rows
  - SCD 2 in action:      5 customer address changes -> old rows expired,
                           new rows inserted in DIM_Customer on next ETL

Run:
    python python/data_gen/generate_incremental_data.py
Then re-run the ETL (run.py option 2) to load the changes into the DWH.
"""

import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from db import connect, PLACEHOLDER
from generate_data import (
    fake,
    load_plz_mapping,
    insert_customers,
    insert_orders,
    random_order_date,
    _unique_email,
    COLOURS,
    MATERIALS,
    PAYMENT_METHODS,
    PAYMENT_WEIGHTS,
)

# ---------------------------------------------------------------------------
# Demo seed -- different from the initial seed so we get different names/data
# ---------------------------------------------------------------------------
DEMO_SEED = 99
random.seed(DEMO_SEED)

# ---------------------------------------------------------------------------
# New suppliers (countries not yet in the original 20)
# ---------------------------------------------------------------------------
NEW_SUPPLIERS: list[tuple[str, str, str]] = [
    ("ItalianDesign S.r.l.", "Milano",  "Italy"),
    ("CzechFurniture s.r.o.", "Praha", "Czech Republic"),
]

# ---------------------------------------------------------------------------
# New products -- one per new supplier; assigned to existing sub-categories
# We hard-code realistic names so they stand out in demos.
# ---------------------------------------------------------------------------
# (ProductName, ListPrice, Colour, Material, sub_category_name)
NEW_PRODUCTS: list[tuple[str, float, str, str, str]] = [
    ("Eleganza Sofa Milano",   1299.99, "Beige",  "Echtleder",  "Sofas & Couches"),
    ("Praha Office Chair Pro",  449.00, "Schwarz", "Kunstleder", "Buerostuehle"),
]

# Number of addresses to change (must be <= existing customer count)
N_ADDRESS_CHANGES = 5


def insert_new_suppliers(conn) -> list[int]:
    """Insert NEW_SUPPLIERS if not already present; return their SupplierId values."""
    ids = []
    for name, city, country in NEW_SUPPLIERS:
        existing = conn.execute(
            "SELECT SupplierId FROM Supplier WHERE SupplierName=? AND City=? AND Country=?",
            (name, city, country),
        ).fetchone()
        if existing:
            ids.append(existing[0])
            print(f"    Supplier already exists: {name} ({city}, {country})  id={existing[0]}")
        else:
            cur = conn.execute(
                f"INSERT INTO Supplier (SupplierName, City, Country) "
                f"VALUES ({PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER})",
                (name, city, country),
            )
            ids.append(cur.lastrowid)
            print(f"    Supplier inserted: {name} ({city}, {country})  id={cur.lastrowid}")
    conn.commit()
    return ids


def insert_new_products(conn, supplier_ids: list[int]) -> list[int]:
    """Insert NEW_PRODUCTS if not already present; return their ProductId values."""
    ids = []
    for (name, price, colour, material, sub_cat), sup_id in zip(NEW_PRODUCTS, supplier_ids):
        existing = conn.execute(
            "SELECT ProductId FROM Product WHERE ProductName=?", (name,)
        ).fetchone()
        if existing:
            ids.append(existing[0])
            print(f"    Product already exists: '{name}'  id={existing[0]}")
            continue
        cat_row = conn.execute(
            "SELECT CategoryId FROM Category WHERE CategoryName = ?",
            (sub_cat,),
        ).fetchone()
        if cat_row is None:
            print(f"    WARNING: sub-category '{sub_cat}' not found -- skipping product '{name}'")
            continue
        cat_id = cat_row[0]
        cur = conn.execute(
            f"INSERT INTO Product (ProductName, ListPrice, Colour, Material, CategoryId, SupplierId) "
            f"VALUES ({PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER})",
            (name, price, colour, material, cat_id, sup_id),
        )
        ids.append(cur.lastrowid)
        print(f"    Product inserted: '{name}'  id={cur.lastrowid}")
    conn.commit()
    return ids


def change_customer_addresses(conn, plz_rows: list[dict], n: int = 5) -> list[int]:
    """
    Pick n random existing customers and update their PostalCode, City,
    FederalState, and StreetAddress to a different PLZ.
    Tries to move to a different FederalState so SCD 2 is meaningful.
    Returns list of updated CustomerIds.
    """
    all_customers = conn.execute(
        "SELECT CustomerId, FederalState FROM Customer ORDER BY RANDOM() LIMIT ?", (n * 3,)
    ).fetchall()

    updated_ids: list[int] = []
    for row in all_customers:
        if len(updated_ids) >= n:
            break
        cid   = row["CustomerId"]
        old_state = row["FederalState"]
        # Pick a PLZ from a *different* federal state when possible
        candidates = [p for p in plz_rows if p["FederalState"] != old_state]
        if not candidates:
            candidates = plz_rows
        new_plz = random.choice(candidates)
        new_street = fake.street_address()
        conn.execute(
            f"UPDATE Customer SET PostalCode={PLACEHOLDER}, City={PLACEHOLDER}, "
            f"FederalState={PLACEHOLDER}, StreetAddress={PLACEHOLDER} "
            f"WHERE CustomerId={PLACEHOLDER}",
            (new_plz["PostalCode"], new_plz["City"],
             new_plz["FederalState"], new_street, cid),
        )
        print(f"    Address changed: CustomerId={cid}  "
              f"{old_state} -> {new_plz['FederalState']}  "
              f"new PLZ={new_plz['PostalCode']}")
        updated_ids.append(cid)
    conn.commit()
    return updated_ids


def main() -> None:
    plz_rows = load_plz_mapping()
    conn = connect()
    try:
        # ------------------------------------------------------------------
        print("\n[1/5] Inserting 2 new suppliers ...")
        new_supplier_ids = insert_new_suppliers(conn)

        # ------------------------------------------------------------------
        print("\n[2/5] Inserting 2 new products ...")
        new_product_ids = insert_new_products(conn, new_supplier_ids)

        # ------------------------------------------------------------------
        print("\n[3/5] Inserting 10 new customers ...")
        new_customer_records = insert_customers(conn, plz_rows, n=10)
        print(f"    {len(new_customer_records)} customers inserted.")

        # ------------------------------------------------------------------
        print("\n[4/5] Inserting 100 new orders (mixed existing + new customers) ...")
        all_customer_ids = [
            r[0]
            for r in conn.execute("SELECT CustomerId, CustomerSince FROM Customer").fetchall()
        ]
        # Build (CustomerId, CustomerSince) records for all customers
        all_customer_records = [
            (r["CustomerId"], r["CustomerSince"])
            for r in conn.execute("SELECT CustomerId, CustomerSince FROM Customer")
        ]
        all_product_ids = [
            r[0] for r in conn.execute("SELECT ProductId FROM Product")
        ]
        insert_orders(conn, all_customer_records, all_product_ids, n_orders=100)
        print(f"    100 orders inserted.")

        # ------------------------------------------------------------------
        print(f"\n[5/5] Changing {N_ADDRESS_CHANGES} customer addresses (SCD 2 trigger) ...")
        changed_ids = change_customer_addresses(conn, plz_rows, n=N_ADDRESS_CHANGES)

        # ------------------------------------------------------------------
        print("\n--- Delta Summary ---")
        n_sup = conn.execute("SELECT COUNT(*) FROM Supplier").fetchone()[0]
        n_pro = conn.execute("SELECT COUNT(*) FROM Product").fetchone()[0]
        n_cus = conn.execute("SELECT COUNT(*) FROM Customer").fetchone()[0]
        n_ohd = conn.execute("SELECT COUNT(*) FROM OrderHeader").fetchone()[0]
        n_oli = conn.execute("SELECT COUNT(*) FROM OrderLine").fetchone()[0]
        print(f"  Supplier     : {n_sup}")
        print(f"  Product      : {n_pro}")
        print(f"  Customer     : {n_cus}")
        print(f"  OrderHeader  : {n_ohd}")
        print(f"  OrderLine    : {n_oli}")
        print(f"\n  {N_ADDRESS_CHANGES} customer addresses changed (SCD 2 triggers on next ETL).")
        print("  -> Run the ETL (run.py option 2) to load these changes into the DWH.\n")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
