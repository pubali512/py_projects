"""
Synthetic data generation for the Online Furniture Business DB.

Targets:
  - 20 suppliers
  - 10 categories (5 top-level, 5 sub-categories)
  - 120 products
  - 5,000 customers  (PLZ-City-state from curated mapping)
  - 30,000 orders    (2024-01-01 - 2025-12-31)
  - ~69,000 order lines (~2.3 per order on average)

Run:
    python python/data_gen/generate_data.py
"""

import csv
import importlib.util
import pathlib
import random
import sqlite3
import subprocess
import sys
from datetime import date, timedelta

# -- Auto-install missing dependencies into the running Python -----------------
def _ensure(package: str) -> None:
    if importlib.util.find_spec(package) is None:
        print(f"  Package '{package}' not found -- installing for {sys.executable} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

_ensure("faker")
# -----------------------------------------------------------------------------

from faker import Faker

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect, PLACEHOLDER

# -- Reproducible seed --------------------------------------------------------
SEED = 42
random.seed(SEED)
fake = Faker("de_DE")
Faker.seed(SEED)

# -- Paths --------------------------------------------------------------------
ROOT = pathlib.Path(__file__).parent.parent.parent
SQL_DDL = ROOT / "sql" / "01_create_business_db.sql"
PLZ_CSV = ROOT / "data" / "plz_city_mapping.csv"

# -- Reference data ------------------------------------------------------------
PAYMENT_METHODS = ["credit_card", "paypal", "bank_transfer", "invoice"]
PAYMENT_WEIGHTS = [0.35, 0.30, 0.20, 0.15]

COLOURS   = ["Weiss", "Schwarz", "Grau", "Beige", "Braun", "Eiche", "Natur",
             "Anthrazit", "Blau", "Gruen"]
MATERIALS = ["Massivholz", "MDF", "Spanplatte", "Metall", "Polster",
             "Kunstleder", "Echtleder", "Glas", "Bambus", "Kunststoff"]

# Top-level categories -> sub-categories
CATEGORY_TREE = {
    "Wohnzimmer":   ["Sofas & Couches", "Couchtische"],
    "Schlafzimmer": ["Betten & Matratzen", "Kleiderschraenke"],
    "Esszimmer":    ["Esstische", "Stuehle & Baenke"],
    "Buero":         ["Schreibtische", "Buerostuehle"],
    "Kinderzimmer": ["Kinderbetten", "Spielmoebel"],
}

# Product name templates per top-level Category
PRODUCT_TEMPLATES = {
    "Wohnzimmer":   ["Sofa {adj}", "Couch {adj}", "Couchtisch {adj}",
                     "Regal {adj}", "TV-Board {adj}"],
    "Schlafzimmer": ["Bett {adj}", "Kleiderschrank {adj}", "Kommode {adj}",
                     "Nachttisch {adj}", "Lattenrost {adj}"],
    "Esszimmer":    ["Esstisch {adj}", "Essstuhl {adj}", "Sitzbank {adj}",
                     "Buffet {adj}", "Barhocker {adj}"],
    "Buero":         ["Schreibtisch {adj}", "Buerostuhl {adj}", "Aktenschrank {adj}",
                     "Regalwand {adj}", "Rollcontainer {adj}"],
    "Kinderzimmer": ["Kinderbett {adj}", "Spieltisch {adj}", "Regal {adj}",
                     "Wickelkommode {adj}", "Hochbett {adj}"],
}

ADJECTIVES = ["Classic", "Modern", "Premium", "Comfort", "Slim", "XL",
              "Eco", "Vintage", "Urban", "Loft", "Compact", "Deluxe",
              "Essential", "Pro", "Soft"]

# Each tuple: (SupplierName, City, Country)
# ~50% Germany, remaining split across neighboring countries
SUPPLIERS: list[tuple[str, str, str]] = [
    # Germany (10)
    ("Holzwerk GmbH",            "Hamburg",              "Germany"),
    ("MoebelDesign AG",           "Muenchen",              "Germany"),
    ("NaturMoebel AG",            "Stuttgart",            "Germany"),
    ("FurnitureFirst GmbH",      "Koeln",                 "Germany"),
    ("DesignHaus AG",            "Frankfurt am Main",    "Germany"),
    ("WohnKultur GmbH",          "Duesseldorf",           "Germany"),
    ("KomfortWelt KG",           "Berlin",               "Germany"),
    ("ClassicHome GmbH",         "Leipzig",              "Germany"),
    ("UrbanLiving KG",           "Hannover",             "Germany"),
    ("GruenesMoebelhaus GmbH",     "Freiburg im Breisgau", "Germany"),
    # Austria (3)
    ("WienerMoebel GmbH",         "Wien",                 "Austria"),
    ("AlpenDesign AG",           "Graz",                 "Austria"),
    ("SalzburgHome GmbH",        "Salzburg",             "Austria"),
    # Switzerland (2)
    ("SwissFurniture AG",         "Zuerich",               "Switzerland"),
    ("BaselWohn AG",              "Basel",                "Switzerland"),
    # Netherlands (2)
    ("DutchDesign B.V.",          "Amsterdam",            "Netherlands"),
    ("HollandHout B.V.",          "Eindhoven",            "Netherlands"),
    # Belgium (2)
    ("BelgianCraft N.V.",         "Antwerpen",            "Belgium"),
    ("MeubelHuis B.V.B.A.",       "Gent",                 "Belgium"),
    # France (1)
    ("MaisonDesign S.A.S.",       "Strasbourg",           "France"),
]


# -- Helpers -------------------------------------------------------------------
_EMAIL_DOMAINS = [
    "gmail.com", "gmx.de", "web.de", "yahoo.com", "t-online.de",
    "hotmail.com", "outlook.com", "freenet.de", "arcor.de", "vodafone.de",
    "icloud.com", "yahoo.de", "googlemail.com", "live.de", "online.de",
]

def _name_part(name: str) -> str:
    """Lowercase, umlaut-replaced, ASCII-only alphabetic characters from a name.
    Uses escape sequences so this function is unaffected by ASCII cleanup scripts.
    """
    s = name.lower()
    # German umlauts via Unicode escape sequences (not literal characters)
    s = (s.replace('\u00e4', 'ae')   # ae
          .replace('\u00f6', 'oe')   # oe
          .replace('\u00fc', 'ue')   # ue
          .replace('\u00df', 'ss')   # ss
          .replace('\u00c4', 'ae')   # Ae -> ae (already lowercased)
          .replace('\u00d6', 'oe')   # Oe -> oe
          .replace('\u00dc', 'ue')   # Ue -> ue
          .replace(' ', '').replace('-', '').replace("'", ''))
    s = s.encode('ascii', errors='ignore').decode('ascii')
    return ''.join(c for c in s if c.isalpha())


def generate_email(FirstName: str, LastName: str) -> str:
    """Generate a realistic Email address based on first and last name.

    Format options:
        <first>.<last>          ->  max.mustermann
        <first>.<last[0]>       ->  max.m
        <first>_<last>          ->  max_mustermann
        <first[0]><last>        ->  mmustermann
        <first[0]>_<last>       ->  m_mustermann
    In 1 out of 10 cases a random 2-4 digit number is appended.
    """
    fn = _name_part(FirstName)
    ln = _name_part(LastName)
    if not fn:
        fn = "user"
    if not ln:
        ln = str(random.randint(100, 999))

    local = random.choice([
        f"{fn}.{ln}",
        f"{fn}.{ln[0]}",
        f"{fn}_{ln}",
        f"{fn[0]}{ln}",
        f"{fn[0]}_{ln}",
    ])
    if random.random() < 0.10:
        local += str(random.randint(10, 9999))

    return f"{local}@{random.choice(_EMAIL_DOMAINS)}"


def _unique_email(FirstName: str, LastName: str, used: set[str]) -> str:
    """Generate an Email from name; append counter suffix if already used."""
    Email = generate_email(FirstName, LastName)
    if Email not in used:
        return Email
    local, domain = Email.rsplit("@", 1)
    counter = 1
    while True:
        candidate = f"{local}{counter}@{domain}"
        if candidate not in used:
            return candidate
        counter += 1


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
    """Customer registered between 5 years before and on the same Day as first order."""
    OrderDate = date.fromisoformat(order_date_str)
    earliest   = OrderDate - timedelta(days=5 * 365)
    delta      = (OrderDate - earliest).days
    return (earliest + timedelta(days=random.randint(0, delta))).isoformat()


# -- DDL -----------------------------------------------------------------------

def apply_ddl(conn: sqlite3.Connection) -> None:
    ddl = SQL_DDL.read_text(encoding="utf-8")
    conn.executescript(ddl)
    conn.commit()


# -- Insert helpers -------------------------------------------------------------

def insert_suppliers(conn: sqlite3.Connection) -> list[int]:
    ids = []
    for name, City, Country in SUPPLIERS:
        cur = conn.execute(
            f"INSERT INTO Supplier (SupplierName, City, Country) VALUES ({PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER})",
            (name, City, Country),
        )
        ids.append(cur.lastrowid)
    conn.commit()
    return ids


def insert_categories(conn: sqlite3.Connection) -> dict[str, int]:
    """Returns mapping: CategoryName -> CategoryId (all levels)."""
    cat_ids: dict[str, int] = {}
    for top_name, sub_names in CATEGORY_TREE.items():
        cur = conn.execute(
            f"INSERT INTO Category (CategoryName, ParentCategoryId) VALUES ({PLACEHOLDER}, NULL)",
            (top_name,),
        )
        top_id = cur.lastrowid
        cat_ids[top_name] = top_id
        for sub_name in sub_names:
            cur = conn.execute(
                f"INSERT INTO Category (CategoryName, ParentCategoryId) VALUES ({PLACEHOLDER},{PLACEHOLDER})",
                (sub_name, top_id),
            )
            cat_ids[sub_name] = cur.lastrowid
    conn.commit()
    return cat_ids


def insert_products(conn: sqlite3.Connection, cat_ids: dict[str, int],
                    supplier_ids: list[int]) -> list[int]:
    ids = []
    used_names: set[str] = set()
    products_per_top = 24  # 5 top categories * 24 ~ 120

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
            # Assign to a sub-Category (or the top-level if no sub exists)
            cat_name = random.choice(all_subs) if all_subs else top_name
            cat_id   = cat_ids[cat_name]
            sup_id   = random.choice(supplier_ids)
            ListPrice = round(random.uniform(49.99, 2499.99), 2)
            Colour   = random.choice(COLOURS)
            Material = random.choice(MATERIALS)
            cur = conn.execute(
                f"INSERT INTO Product (ProductName, ListPrice, Colour, Material, CategoryId, SupplierId) "
                f"VALUES ({PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER},{PLACEHOLDER})",
                (name, ListPrice, Colour, Material, cat_id, sup_id),
            )
            ids.append(cur.lastrowid)
            generated += 1
    conn.commit()
    return ids


def insert_customers(conn: sqlite3.Connection, plz_rows: list[dict],
                     n: int = 5_000) -> list[tuple[int, str]]:
    """Returns list of (CustomerId, CustomerSince) for order generation."""
    result = []
    used_emails: set[str] = set()
    inserted = 0
    while inserted < n:
        plz_row   = random.choice(plz_rows)
        plz       = plz_row["PostalCode"]
        City      = plz_row["City"]
        state     = plz_row["FederalState"]
        first     = fake.first_name()
        last      = fake.last_name()
        Email     = _unique_email(first, last, used_emails)
        used_emails.add(Email)
        street    = fake.street_address()
        dummy_date = random_order_date()
        since = random_customer_since(dummy_date)
        cur = conn.execute(
            f"INSERT INTO Customer "
            f"(FirstName, LastName, Email, StreetAddress, PostalCode, City, FederalState, CustomerSince) "
            f"VALUES ({','.join([PLACEHOLDER]*8)})",
            (first, last, Email, street, plz, City, state, since),
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
        OrderDate  = random_order_date()
        payment     = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS, k=1)[0]
        shipping    = round(random.choice([0.0, 4.99, 6.99, 9.99]), 2)
        order_batch.append((OrderDate, payment, shipping, cust_id))
        order_id_counter += 1

        # 1-5 lines per order; weighted toward 2-3
        n_lines = random.choices([1, 2, 3, 4, 5], weights=[10, 30, 35, 15, 10], k=1)[0]
        chosen_products = random.sample(product_ids, min(n_lines, len(product_ids)))
        for prod_id in chosen_products:
            qty       = random.randint(1, 4)
            # UnitPrice is ListPrice +/- 10% (simulates dynamic pricing)
            row = conn.execute("SELECT ListPrice FROM Product WHERE ProductId = ?", (prod_id,)).fetchone()
            base_price = row[0]
            UnitPrice = round(base_price * random.uniform(0.90, 1.10), 2)
            # Discount: 80% of lines have 0%, rest up to 25%
            Discount = round(random.choices(
                [0.0, random.uniform(0.05, 0.25)],
                weights=[80, 20], k=1)[0], 2)
            line_batch.append((qty, UnitPrice, Discount, order_id_counter, prod_id))

    conn.executemany(
        f"INSERT INTO OrderHeader (OrderDate, PaymentMethod, ShippingCost, CustomerId) "
        f"VALUES ({','.join([PLACEHOLDER]*4)})",
        order_batch,
    )
    conn.executemany(
        f"INSERT INTO OrderLine (Quantity, UnitPrice, Discount, OrderId, ProductId) "
        f"VALUES ({','.join([PLACEHOLDER]*5)})",
        line_batch,
    )
    conn.commit()


# -- Main ----------------------------------------------------------------------

def main() -> None:
    plz_rows = load_plz_mapping()
    print(f"Loaded {len(plz_rows)} PLZ rows from mapping file.")

    conn = connect()
    print("Applying DDL ...")
    apply_ddl(conn)

    print("Inserting suppliers ...")
    supplier_ids = insert_suppliers(conn)
    print(f"  {len(supplier_ids)} suppliers")

    print("Inserting categories ...")
    cat_ids = insert_categories(conn)
    print(f"  {len(cat_ids)} categories ({len(CATEGORY_TREE)} top-level)")

    print("Inserting products ...")
    product_ids = insert_products(conn, cat_ids, supplier_ids)
    print(f"  {len(product_ids)} products")

    print("Inserting customers ...")
    customer_records = insert_customers(conn, plz_rows, n=5_000)
    print(f"  {len(customer_records)} customers")

    print("Inserting orders and order lines ...")
    insert_orders(conn, customer_records, product_ids, n_orders=30_000)

    # Summary
    row = conn.execute("SELECT COUNT(*) FROM OrderHeader").fetchone()
    print(f"  {row[0]} orders")
    row = conn.execute("SELECT COUNT(*) FROM OrderLine").fetchone()
    print(f"  {row[0]} order lines")

    conn.close()
    print("Done. Database written to data/furniture.db")


if __name__ == "__main__":
    main()
