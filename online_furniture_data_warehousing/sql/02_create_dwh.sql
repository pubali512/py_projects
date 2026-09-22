-- =============================================================================
-- DWH DDL  |  Online Furniture Retailer -- Star Schema
-- Tables: dim_date, dim_customer (SCD 2), dim_product, dim_supplier, fact_sales
-- Staging tables follow naming convention RAW_ / FULL_
-- =============================================================================

PRAGMA foreign_keys = ON;

-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- dim_date
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_sk         INTEGER PRIMARY KEY,   -- surrogate key: YYYYMMDD integer
    full_date       TEXT    NOT NULL UNIQUE,
    day             INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      TEXT    NOT NULL,
    quarter         INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    weekday         INTEGER NOT NULL,      -- 0 = Monday ... 6 = Sunday
    weekday_name    TEXT    NOT NULL,
    calendar_week   INTEGER NOT NULL
);

-- -----------------------------------------------------------------------------
-- dim_customer  (SCD Type 2 -- tracks address / postal_code changes)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_sk     INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL,      -- natural key from Business DB
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email           TEXT    NOT NULL,
    street_address  TEXT    NOT NULL,
    postal_code     TEXT    NOT NULL,
    plz_region      TEXT    NOT NULL,      -- first digit of postal_code (0-9)
    plz_zone        TEXT    NOT NULL,      -- first two digits of postal_code
    city            TEXT    NOT NULL,
    federal_state   TEXT    NOT NULL,
    valid_from      TEXT    NOT NULL,      -- ISO date YYYY-MM-DD
    valid_to        TEXT,                  -- NULL = currently active row
    is_current      INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_dim_customer_natural  ON dim_customer(customer_id);
CREATE INDEX IF NOT EXISTS idx_dim_customer_current  ON dim_customer(customer_id, is_current);

-- -----------------------------------------------------------------------------
-- dim_product
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_product (
    product_sk      INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL UNIQUE,   -- natural key (SCD 1 -- overwrite)
    product_name    TEXT    NOT NULL,
    colour          TEXT,
    material        TEXT,
    list_price      REAL    NOT NULL,
    category_name   TEXT    NOT NULL,          -- sub-category
    top_category_name TEXT  NOT NULL           -- top-level category
);

-- -----------------------------------------------------------------------------
-- dim_supplier
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_supplier (
    supplier_sk     INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id     INTEGER NOT NULL UNIQUE,   -- natural key
    supplier_name   TEXT    NOT NULL,
    city            TEXT    NOT NULL,
    country         TEXT    NOT NULL
);

-- =============================================================================
-- FACT TABLE
-- =============================================================================

-- -----------------------------------------------------------------------------
-- fact_sales  (grain: one row per order line)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_sales (
    sales_sk        INTEGER PRIMARY KEY AUTOINCREMENT,
    date_sk         INTEGER NOT NULL REFERENCES dim_date(date_sk),
    customer_sk     INTEGER NOT NULL REFERENCES dim_customer(customer_sk),
    product_sk      INTEGER NOT NULL REFERENCES dim_product(product_sk),
    supplier_sk     INTEGER NOT NULL REFERENCES dim_supplier(supplier_sk),
    order_id        INTEGER NOT NULL,      -- degenerate dimension
    quantity        INTEGER NOT NULL,
    gross_amount    REAL    NOT NULL,      -- quantity * unit_price
    discount_amount REAL    NOT NULL,      -- gross_amount * discount
    net_amount      REAL    NOT NULL,      -- gross_amount - discount_amount
    shipping_cost   REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_date     ON fact_sales(date_sk);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON fact_sales(customer_sk);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product  ON fact_sales(product_sk);
CREATE INDEX IF NOT EXISTS idx_fact_sales_supplier ON fact_sales(supplier_sk);

-- =============================================================================
-- STAGING TABLES  (RAW layer -- direct copy from Business DB)
-- =============================================================================

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_Customer (
    customer_id     INTEGER,
    first_name      TEXT,
    last_name       TEXT,
    email           TEXT,
    street_address  TEXT,
    postal_code     TEXT,
    city            TEXT,
    federal_state   TEXT,
    customer_since  TEXT
);

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_OrderHeader (
    order_id        INTEGER,
    order_date      TEXT,
    payment_method  TEXT,
    shipping_cost   REAL,
    customer_id     INTEGER
);

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_OrderLine (
    order_line_id   INTEGER,
    quantity        INTEGER,
    unit_price      REAL,
    discount        REAL,
    order_id        INTEGER,
    product_id      INTEGER
);

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_Product (
    product_id      INTEGER,
    product_name    TEXT,
    list_price      REAL,
    colour          TEXT,
    material        TEXT,
    category_id     INTEGER,
    supplier_id     INTEGER
);

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_Category (
    category_id        INTEGER,
    category_name      TEXT,
    parent_category_id INTEGER
);

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_Supplier (
    supplier_id     INTEGER,
    supplier_name   TEXT,
    city            TEXT,
    country         TEXT
);

-- =============================================================================
-- STAGING TABLES  (FULL layer -- cleansed and enriched)
-- =============================================================================

CREATE TABLE IF NOT EXISTS FULL_BusinessDB_DWH_Customer (
    customer_id     INTEGER,
    first_name      TEXT,
    last_name       TEXT,
    email           TEXT,
    street_address  TEXT,
    postal_code     TEXT,
    plz_region      TEXT,
    plz_zone        TEXT,
    city            TEXT,
    federal_state   TEXT,
    customer_since  TEXT
);

CREATE TABLE IF NOT EXISTS FULL_BusinessDB_DWH_Product (
    product_id        INTEGER,
    product_name      TEXT,
    colour            TEXT,
    material          TEXT,
    list_price        REAL,
    category_name     TEXT,
    top_category_name TEXT,
    supplier_id       INTEGER
);

CREATE TABLE IF NOT EXISTS FULL_BusinessDB_DWH_Sales (
    order_line_id   INTEGER,
    order_id        INTEGER,
    order_date      TEXT,
    customer_id     INTEGER,
    product_id      INTEGER,
    supplier_id     INTEGER,
    quantity        INTEGER,
    unit_price      REAL,
    discount        REAL,
    shipping_cost   REAL,
    gross_amount    REAL,
    discount_amount REAL,
    net_amount      REAL
);
