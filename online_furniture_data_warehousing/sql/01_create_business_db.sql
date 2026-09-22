-- =============================================================================
-- Business DB DDL  |  Online Furniture Retailer
-- Normalisation: 3NF
-- Tables: supplier, category, product, customer, order_header, order_line
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- supplier
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS supplier (
    supplier_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT    NOT NULL,
    city          TEXT    NOT NULL,
    country       TEXT    NOT NULL DEFAULT 'Germany'
);

-- -----------------------------------------------------------------------------
-- category  (two-level hierarchy via self-referencing FK)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS category (
    category_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name      TEXT    NOT NULL UNIQUE,
    parent_category_id INTEGER REFERENCES category(category_id)
);

-- -----------------------------------------------------------------------------
-- product
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product (
    product_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name  TEXT    NOT NULL,
    list_price    REAL    NOT NULL CHECK (list_price > 0),
    colour        TEXT,
    material      TEXT,
    category_id   INTEGER NOT NULL REFERENCES category(category_id),
    supplier_id   INTEGER NOT NULL REFERENCES supplier(supplier_id)
);

-- -----------------------------------------------------------------------------
-- customer
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer (
    customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE,
    street_address  TEXT    NOT NULL,
    postal_code     TEXT    NOT NULL,
    city            TEXT    NOT NULL,
    federal_state   TEXT    NOT NULL,
    customer_since  TEXT    NOT NULL   -- ISO date string YYYY-MM-DD
);

-- -----------------------------------------------------------------------------
-- order_header
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_header (
    order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    order_date      TEXT    NOT NULL,  -- ISO date string YYYY-MM-DD
    payment_method  TEXT    NOT NULL CHECK (payment_method IN (
                        'credit_card', 'paypal', 'bank_transfer', 'invoice')),
    shipping_cost   REAL    NOT NULL CHECK (shipping_cost >= 0),
    customer_id     INTEGER NOT NULL REFERENCES customer(customer_id)
);

-- -----------------------------------------------------------------------------
-- order_line
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_line (
    order_line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    REAL    NOT NULL CHECK (unit_price > 0),
    discount      REAL    NOT NULL CHECK (discount >= 0 AND discount < 1),
    order_id      INTEGER NOT NULL REFERENCES order_header(order_id),
    product_id    INTEGER NOT NULL REFERENCES product(product_id)
);

-- -----------------------------------------------------------------------------
-- Indexes for common join / filter columns
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_order_header_customer ON order_header(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_header_date     ON order_header(order_date);
CREATE INDEX IF NOT EXISTS idx_order_line_order      ON order_line(order_id);
CREATE INDEX IF NOT EXISTS idx_order_line_product    ON order_line(product_id);
CREATE INDEX IF NOT EXISTS idx_product_category      ON product(category_id);
CREATE INDEX IF NOT EXISTS idx_product_supplier      ON product(supplier_id);
