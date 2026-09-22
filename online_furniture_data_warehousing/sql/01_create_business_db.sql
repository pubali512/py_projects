-- =============================================================================
-- Business DB DDL  |  Online Furniture Retailer
-- Normalisation: 3NF
-- Tables: Supplier, Category, Product, Customer, OrderHeader, OrderLine
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- Supplier
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Supplier (
    supplier_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT    NOT NULL,
    city          TEXT    NOT NULL,
    country       TEXT    NOT NULL DEFAULT 'Germany'
);

-- -----------------------------------------------------------------------------
-- Category  (two-level hierarchy via self-referencing FK)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Category (
    category_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name      TEXT    NOT NULL UNIQUE,
    parent_category_id INTEGER REFERENCES Category(category_id)
);

-- -----------------------------------------------------------------------------
-- Product
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Product (
    product_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name  TEXT    NOT NULL,
    list_price    REAL    NOT NULL CHECK (list_price > 0),
    colour        TEXT,
    material      TEXT,
    category_id   INTEGER NOT NULL REFERENCES Category(category_id),
    supplier_id   INTEGER NOT NULL REFERENCES Supplier(supplier_id)
);

-- -----------------------------------------------------------------------------
-- Customer
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Customer (
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
-- OrderHeader
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS OrderHeader (
    order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    order_date      TEXT    NOT NULL,  -- ISO date string YYYY-MM-DD
    payment_method  TEXT    NOT NULL CHECK (payment_method IN (
                        'credit_card', 'paypal', 'bank_transfer', 'invoice')),
    shipping_cost   REAL    NOT NULL CHECK (shipping_cost >= 0),
    customer_id     INTEGER NOT NULL REFERENCES Customer(customer_id)
);

-- -----------------------------------------------------------------------------
-- OrderLine
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS OrderLine (
    order_line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    REAL    NOT NULL CHECK (unit_price > 0),
    discount      REAL    NOT NULL CHECK (discount >= 0 AND discount < 1),
    order_id      INTEGER NOT NULL REFERENCES OrderHeader(order_id),
    product_id    INTEGER NOT NULL REFERENCES Product(product_id)
);

-- -----------------------------------------------------------------------------
-- Indexes for common join / filter columns
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_order_header_customer ON OrderHeader(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_header_date     ON OrderHeader(order_date);
CREATE INDEX IF NOT EXISTS idx_order_line_order      ON OrderLine(order_id);
CREATE INDEX IF NOT EXISTS idx_order_line_product    ON OrderLine(product_id);
CREATE INDEX IF NOT EXISTS idx_product_category      ON Product(category_id);
CREATE INDEX IF NOT EXISTS idx_product_supplier      ON Product(supplier_id);
