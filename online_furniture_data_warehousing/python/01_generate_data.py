"""
Synthetic data generation for the Online Furniture Business DB.

Targets:
  - 20 suppliers
  - 10 categories (5 top-level, 5 sub-categories)
  - 120 products
  - 5,000 customers  (PLZ-city-state from curated mapping)
  - 30,000 orders    (2024-01-01 – 2025-12-31)
  - ~69,000 order lines (~2.3 per order on average)

Run:
    python python/01_generate_data.py
"""

import csv
import pathlib
import random
import sqlite3
from datetime import date, timedelta

from faker import Faker

import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from db import connect, PLACEHOLDER

# ── Reproducible seed ────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
fake = Faker("de_DE")
Faker.seed(SEED)

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).parent.parent
SQL_DDL = ROOT / "sql" / "01_create_business_db.sql"
PLZ_CSV = ROOT / "data" / "plz_city_mapping.csv"

# ── Reference data ────────────────────────────────────────────────────────────
PAYMENT_METHODS = ["credit_card", "paypal", "bank_transfer", "invoice"]
PAYMENT_WEIGHTS = [0.35, 0.30, 0.20, 0.15]

COLOURS   = ["Weiß", "Schwarz", "Grau", "Beige", "Braun", "Eiche", "Natur",
             "Anthrazit", "Blau", "Grün"]
MATERIALS = ["Massivholz", "MDF", "Spanplatte", "Metall", "Polster",
             "Kunstleder", "Echtleder", "Glas", "Bambus", "Kunststoff"]

# Top-level categories → sub-categories
CATEGORY_TREE = {
    "Wohnzimmer":   ["Sofas & Couches", "Couchtische"],
    "Schlafzimmer": ["Betten & Matratzen", "Kleiderschränke"],
    "Esszimmer":    ["Esstische", "Stühle & Bänke"],
    "Büro":         ["Schreibtische", "Bürostühle"],
    "Kinderzimmer": ["Kinderbetten", "Spielmöbel"],
}

# Product name templates per top-level category
PRODUCT_TEMPLATES = {
    "Wohnzimmer":   ["Sofa {adj}", "Couch {adj}", "Couchtisch {adj}",
                     "Regal {adj}", "TV-Board {adj}"],
    "Schlafzimmer": ["Bett {adj}", "Kleiderschrank {adj}", "Kommode {adj}",
                     "Nachttisch {adj}", "Lattenrost {adj}"],
    "Esszimmer":    ["Esstisch {adj}", "Essstuhl {adj}", "Sitzbank {adj}",
                     "Buffet {adj}", "Barhocker {adj}"],
    "Büro":         ["Schreibtisch {adj}", "Bürostuhl {adj}", "Aktenschrank {adj}",
                     "Regalwand {adj}", "Rollcontainer {adj}"],
    "Kinderzimmer": ["Kinderbett {adj}", "Spieltisch {adj}", "Regal {adj}",
                     "Wickelkommode {adj}", "Hochbett {adj}"],
}

ADJECTIVES = ["Classic", "Modern", "Premium", "Comfort", "Slim", "XL",
              "Eco", "Vintage", "Urban", "Loft", "Compact", "Deluxe",
              "Essential", "Pro", "Soft"]

SUPPLIER_NAMES = [
    "Holzwerk GmbH", "MöbelDesign AG", "EcoFurniture KG",
    "Nordholz OHG", "SüdMöbel GmbH", "WohnKultur GmbH",
    "FurnitureFirst GmbH", "DesignHaus AG", "KomfortWelt KG",
    "HolzWerkstatt GmbH", "ModernWohn OHG", "ClassicHome GmbH",
    "NaturMöbel AG", "UrbanLiving KG", "SleepWell GmbH",
    "KidsFurniture AG", "OfficeStyle KG", "LuxuryHome GmbH",
    "SmartMöbel OHG", "GrünesMöbelhaus GmbH",
]

SUPPLIER_CITIES = [
    "Hamburg", "München", "Berlin", "Köln", "Frankfurt am Main",
    "Stuttgart", "Düsseldorf", "Leipzig", "Dresden", "Hannover",
    "Nürnberg", "Bremen", "Dortmund", "Essen", "Bonn",
    "Mainz", "Erfurt", "Freiburg im Breisgau", "Augsburg", "Kiel",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_plz_mapping() -> list[dict]:
    rows = []
    with open(PLZ_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def random_order_date() -> str:
    start = date(2024, 1, 1)
    end   = date(2025, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def random_customer_since(order_date_str: str) -> str:
    """Customer registered between 5 years before and on the same day as first order."""
    order_date = date.fromisoformat(order_date_str)
    earliest   = order_date - timedelta(days=5 * 365)
    delta      = (order_date - earliest).days
    return (earliest + timedelta(days=random.randint(0, delta))).isoformat()


# ── DDL ───────────────────────────────────────────────────────────────────────

def apply_ddl(conn: sqlite3.Connection) -> None:
    ddl = SQL_DDL.read_text(encoding="utf-8")
    conn.executescript(ddl)
    conn.commit()


# ── Insert helpers ─────────────────────────────────────────────────────────────

def insert_suppliers(conn: sqlite3.Connection) -> list[int]:
    ids = []
    for name, city in zip(SUPPLIER_NAMES, SUPPLIER_CITIES):
        cur = conn.execute(
            f"INSERT INTO supplier (supplier_name, city, country) VALUES ({PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER})",
            (name, city, "Germany"),
        )
        ids.append(cur.lastrowid)
    conn.commit()
    return ids


def insert_categories(conn: sqlite3.Connection) -> dict[str, int]:
    """Returns mapping: category_name → category_id (all levels)."""
    cat_ids: dict[str, int] = {}
    for top_name, sub_names in CATEGORY_TREE.items():
        cur = conn.execute(
            f"INSERT INTO category (category_name, parent_category_id) VALUES ({PLACEHOLDER}, NULL)",
            (top_name,),
        )
        top_id = cur.lastrowid
        cat_ids[top_name] = top_id
        for sub_name in sub_names:
            cur = conn.execute(
                f"INSERT INTO category (category_name, parent_category_id) VALUES ({PLACEHOLDER},{PLACEHOLDER})",
                (sub_name, top_id),
            )
            cat_ids[sub_name] = cur.lastrowid
    conn.commit()
    return cat_ids


def insert_products(conn: sqlite3.Connection, cat_ids: dict[str, int],
                    supplier_ids: list[int]) -> list[int]:
    ids = []
    used_names: set[str] = set()
    products_per_top = 24  # 5 top categories × 24 ≈ 120

    for top_name, templates in PRODUCT_TEMPLATES.items():
        all_subs = CATEGORY_TREE[top_name]
        generated = 0
        while generated < products_per_top:
            template = random.choice(templates)
            adj = random.choice(ADJECTIVES)
            name = template.replace("{adj}", adj)
            if name in used_names:
                continue
            used_names.add(name)
            # Assign to a sub-category (or the top-level if no sub exists)
            cat_name = random.choice(all_subs) if all_subs else top_name
            cat_id   = cat_ids[cat_name]
            sup_id   = random.choice(supplier_ids)
            list_price = round(random.uniform(49.99, 2499.99), 2)
            colour   = random.choice(COLOURS)
            material = random.choice(MATERIALS)
            cur = conn.execute(
                f"INSERT INTO product (product_name, list_price, colour, material, category_id, supplier_id) "
                f"VALUES ({PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER})",
                (name, list_price, colour, material, cat_id, sup_id),
            )
            ids.append(cur.lastrowid)
            generated += 1
    conn.commit()
    return ids


def insert_customers(conn: sqlite3.Connection, plz_rows: list[dict],
                     n: int = 5_000) -> list[tuple[int, str]]:
    """Returns list of (customer_id, customer_since) for order generation."""
    result = []
    used_emails: set[str] = set()
    inserted = 0
    while inserted < n:
        plz_row   = random.choice(plz_rows)
        plz       = plz_row["postal_code"]
        city      = plz_row["city"]
        state     = plz_row["federal_state"]
        email     = fake.email()
        if email in used_emails:
            continue
        used_emails.add(email)
        first     = fake.first_name()
        last      = fake.last_name()
        street    = fake.street_address()
        # customer_since: random date up to 5 years before a dummy order date
        dummy_date = random_order_date()
        since = random_customer_since(dummy_date)
        cur = conn.execute(
            f"INSERT INTO customer "
            f"(first_name, last_name, email, street_address, postal_code, city, federal_state, customer_since) "
            f"VALUES ({','.join([PLACEHOLDER]*8)})",
            (first, last, email, street, plz, city, state, since),
        )
        result.append((cur.lastrowid, since))
        inserted += 1
    conn.commit()
    return result


def insert_orders(conn: sqlite3.Connection,
                  customer_records: list[tuple[int, str]],
                  product_ids: list[int],
                  n_orders: int = 30_000) -> None:
    order_batch: list[tuple] = []
    line_batch:  list[tuple] = []
    order_id_counter = 0

    for _ in range(n_orders):
        cust_id, _ = random.choice(customer_records)
        order_date  = random_order_date()
        payment     = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS, k=1)[0]
        shipping    = round(random.choice([0.0, 4.99, 6.99, 9.99]), 2)
        order_batch.append((order_date, payment, shipping, cust_id))
        order_id_counter += 1

        # 1–5 lines per order; weighted toward 2–3
        n_lines = random.choices([1, 2, 3, 4, 5], weights=[10, 30, 35, 15, 10], k=1)[0]
        chosen_products = random.sample(product_ids, min(n_lines, len(product_ids)))
        for prod_id in chosen_products:
            qty       = random.randint(1, 4)
            # unit_price is list_price ± 10% (simulates dynamic pricing)
            row = conn.execute("SELECT list_price FROM product WHERE product_id = ?", (prod_id,)).fetchone()
            base_price = row[0]
            unit_price = round(base_price * random.uniform(0.90, 1.10), 2)
            # discount: 80% of lines have 0%, rest up to 25%
            discount = round(random.choices(
                [0.0, random.uniform(0.05, 0.25)],
                weights=[80, 20], k=1)[0], 2)
            line_batch.append((qty, unit_price, discount, order_id_counter, prod_id))

    conn.executemany(
        f"INSERT INTO order_header (order_date, payment_method, shipping_cost, customer_id) "
        f"VALUES ({','.join([PLACEHOLDER]*4)})",
        order_batch,
    )
    conn.executemany(
        f"INSERT INTO order_line (quantity, unit_price, discount, order_id, product_id) "
        f"VALUES ({','.join([PLACEHOLDER]*5)})",
        line_batch,
    )
    conn.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    plz_rows = load_plz_mapping()
    print(f"Loaded {len(plz_rows)} PLZ rows from mapping file.")

    conn = connect()
    print("Applying DDL …")
    apply_ddl(conn)

    print("Inserting suppliers …")
    supplier_ids = insert_suppliers(conn)
    print(f"  {len(supplier_ids)} suppliers")

    print("Inserting categories …")
    cat_ids = insert_categories(conn)
    print(f"  {len(cat_ids)} categories ({len(CATEGORY_TREE)} top-level)")

    print("Inserting products …")
    product_ids = insert_products(conn, cat_ids, supplier_ids)
    print(f"  {len(product_ids)} products")

    print("Inserting customers …")
    customer_records = insert_customers(conn, plz_rows, n=5_000)
    print(f"  {len(customer_records)} customers")

    print("Inserting orders and order lines …")
    insert_orders(conn, customer_records, product_ids, n_orders=30_000)

    # Summary
    row = conn.execute("SELECT COUNT(*) FROM order_header").fetchone()
    print(f"  {row[0]} orders")
    row = conn.execute("SELECT COUNT(*) FROM order_line").fetchone()
    print(f"  {row[0]} order lines")

    conn.close()
    print("Done. Database written to data/furniture.db")


if __name__ == "__main__":
    main()
