-- =============================================================================
-- DWH DDL  |  Online Furniture Retailer -- Star Schema
-- Tables: DIM_Date, DIM_Customer (SCD 2), DIM_Product, DIM_Supplier, FACT_Sales
-- Staging tables follow naming convention RAW_ / FULL_
-- =============================================================================

PRAGMA foreign_keys = ON;

-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- DIM_Date
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DIM_Date (
    DateSk         INTEGER PRIMARY KEY,   -- surrogate key: YYYYMMDD integer
    FullDate       TEXT    NOT NULL UNIQUE,
    Day             INTEGER NOT NULL,
    Month           INTEGER NOT NULL,
    MonthName      TEXT    NOT NULL,
    Quarter         INTEGER NOT NULL,
    Year            INTEGER NOT NULL,
    Weekday         INTEGER NOT NULL,      -- 0 = Monday ... 6 = Sunday
    WeekdayName    TEXT    NOT NULL,
    CalendarWeek   INTEGER NOT NULL
);

-- -----------------------------------------------------------------------------
-- DIM_Customer  (SCD Type 2 -- tracks address / PostalCode changes)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DIM_Customer (
    CustomerSk     INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerId     INTEGER NOT NULL,      -- natural key from Business DB
    FirstName      TEXT    NOT NULL,
    LastName       TEXT    NOT NULL,
    Email           TEXT    NOT NULL,
    StreetAddress  TEXT    NOT NULL,
    PostalCode     TEXT    NOT NULL,
    PlzRegion      TEXT    NOT NULL,      -- first digit of PostalCode (0-9)
    PlzZone        TEXT    NOT NULL,      -- first two digits of PostalCode
    City            TEXT    NOT NULL,
    FederalState   TEXT    NOT NULL,
    ValidFrom      TEXT    NOT NULL,      -- ISO date YYYY-MM-DD
    ValidTo        TEXT,                  -- NULL = currently active row
    IsCurrent      INTEGER NOT NULL DEFAULT 1 CHECK (IsCurrent IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_dim_customer_natural  ON DIM_Customer(CustomerId);
CREATE INDEX IF NOT EXISTS idx_dim_customer_current  ON DIM_Customer(CustomerId, IsCurrent);

-- -----------------------------------------------------------------------------
-- DIM_Product
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DIM_Product (
    ProductSk      INTEGER PRIMARY KEY AUTOINCREMENT,
    ProductId      INTEGER NOT NULL UNIQUE,   -- natural key (SCD 1 -- overwrite)
    ProductName    TEXT    NOT NULL,
    Colour          TEXT,
    Material        TEXT,
    ListPrice      REAL    NOT NULL,
    CategoryName   TEXT    NOT NULL,          -- sub-category
    TopCategoryName TEXT  NOT NULL           -- top-level category
);

-- -----------------------------------------------------------------------------
-- DIM_Supplier
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DIM_Supplier (
    SupplierSk     INTEGER PRIMARY KEY AUTOINCREMENT,
    SupplierId     INTEGER NOT NULL UNIQUE,   -- natural key
    SupplierName   TEXT    NOT NULL,
    City            TEXT    NOT NULL,
    Country         TEXT    NOT NULL
);

-- =============================================================================
-- FACT TABLE
-- =============================================================================

-- -----------------------------------------------------------------------------
-- FACT_Sales  (grain: one row per order line)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS FACT_Sales (
    SalesSk        INTEGER PRIMARY KEY AUTOINCREMENT,
    DateSk         INTEGER NOT NULL REFERENCES DIM_Date(DateSk),
    CustomerSk     INTEGER NOT NULL REFERENCES DIM_Customer(CustomerSk),
    ProductSk      INTEGER NOT NULL REFERENCES DIM_Product(ProductSk),
    SupplierSk     INTEGER NOT NULL REFERENCES DIM_Supplier(SupplierSk),
    OrderId        INTEGER NOT NULL,      -- degenerate dimension
    Quantity        INTEGER NOT NULL,
    GrossAmount    REAL    NOT NULL,      -- Quantity * UnitPrice
    DiscountAmount REAL    NOT NULL,      -- GrossAmount * Discount
    NetAmount      REAL    NOT NULL,      -- GrossAmount - DiscountAmount
    ShippingCost   REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_date     ON FACT_Sales(DateSk);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON FACT_Sales(CustomerSk);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product  ON FACT_Sales(ProductSk);
CREATE INDEX IF NOT EXISTS idx_fact_sales_supplier ON FACT_Sales(SupplierSk);

-- =============================================================================
-- STAGING TABLES  (RAW layer -- direct copy from Business DB)
-- =============================================================================

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_Customer (
    CustomerId     INTEGER,
    FirstName      TEXT,
    LastName       TEXT,
    Email           TEXT,
    StreetAddress  TEXT,
    PostalCode     TEXT,
    City            TEXT,
    FederalState   TEXT,
    CustomerSince  TEXT
);

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_OrderHeader (
    OrderId        INTEGER,
    OrderDate      TEXT,
    PaymentMethod  TEXT,
    ShippingCost   REAL,
    CustomerId     INTEGER
);

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_OrderLine (
    OrderLineId   INTEGER,
    Quantity        INTEGER,
    UnitPrice      REAL,
    Discount        REAL,
    OrderId        INTEGER,
    ProductId      INTEGER
);

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_Product (
    ProductId      INTEGER,
    ProductName    TEXT,
    ListPrice      REAL,
    Colour          TEXT,
    Material        TEXT,
    CategoryId     INTEGER,
    SupplierId     INTEGER
);

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_Category (
    CategoryId        INTEGER,
    CategoryName      TEXT,
    ParentCategoryId INTEGER
);

CREATE TABLE IF NOT EXISTS RAW_BusinessDB_Supplier (
    SupplierId     INTEGER,
    SupplierName   TEXT,
    City            TEXT,
    Country         TEXT
);

-- =============================================================================
-- STAGING TABLES  (FULL layer -- cleansed and enriched)
-- =============================================================================

CREATE TABLE IF NOT EXISTS FULL_BusinessDB_DWH_Customer (
    CustomerId     INTEGER,
    FirstName      TEXT,
    LastName       TEXT,
    Email           TEXT,
    StreetAddress  TEXT,
    PostalCode     TEXT,
    PlzRegion      TEXT,
    PlzZone        TEXT,
    City            TEXT,
    FederalState   TEXT,
    CustomerSince  TEXT
);

CREATE TABLE IF NOT EXISTS FULL_BusinessDB_DWH_Product (
    ProductId        INTEGER,
    ProductName      TEXT,
    Colour            TEXT,
    Material          TEXT,
    ListPrice        REAL,
    CategoryName     TEXT,
    TopCategoryName TEXT,
    SupplierId       INTEGER
);

CREATE TABLE IF NOT EXISTS FULL_BusinessDB_DWH_Sales (
    OrderLineId   INTEGER,
    OrderId        INTEGER,
    OrderDate      TEXT,
    CustomerId     INTEGER,
    ProductId      INTEGER,
    SupplierId     INTEGER,
    Quantity        INTEGER,
    UnitPrice      REAL,
    Discount        REAL,
    ShippingCost   REAL,
    GrossAmount    REAL,
    DiscountAmount REAL,
    NetAmount      REAL
);
