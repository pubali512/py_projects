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
    SupplierId   INTEGER PRIMARY KEY AUTOINCREMENT,
    SupplierName TEXT    NOT NULL,
    City          TEXT    NOT NULL,
    Country       TEXT    NOT NULL DEFAULT 'Germany'
);

-- -----------------------------------------------------------------------------
-- Category  (two-level hierarchy via self-referencing FK)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Category (
    CategoryId        INTEGER PRIMARY KEY AUTOINCREMENT,
    CategoryName      TEXT    NOT NULL UNIQUE,
    ParentCategoryId INTEGER REFERENCES Category(CategoryId)
);

-- -----------------------------------------------------------------------------
-- Product
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Product (
    ProductId    INTEGER PRIMARY KEY AUTOINCREMENT,
    ProductName  TEXT    NOT NULL,
    ListPrice    REAL    NOT NULL CHECK (ListPrice > 0),
    Colour        TEXT,
    Material      TEXT,
    CategoryId   INTEGER NOT NULL REFERENCES Category(CategoryId),
    SupplierId   INTEGER NOT NULL REFERENCES Supplier(SupplierId)
);

-- -----------------------------------------------------------------------------
-- Customer
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Customer (
    CustomerId     INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName      TEXT    NOT NULL,
    LastName       TEXT    NOT NULL,
    Email           TEXT    NOT NULL UNIQUE,
    StreetAddress  TEXT    NOT NULL,
    PostalCode     TEXT    NOT NULL,
    City            TEXT    NOT NULL,
    FederalState   TEXT    NOT NULL,
    CustomerSince  TEXT    NOT NULL   -- ISO date string YYYY-MM-DD
);

-- -----------------------------------------------------------------------------
-- OrderHeader
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS OrderHeader (
    OrderId        INTEGER PRIMARY KEY AUTOINCREMENT,
    OrderDate      TEXT    NOT NULL,  -- ISO date string YYYY-MM-DD
    PaymentMethod  TEXT    NOT NULL CHECK (PaymentMethod IN (
                        'credit_card', 'paypal', 'bank_transfer', 'invoice')),
    ShippingCost   REAL    NOT NULL CHECK (ShippingCost >= 0),
    CustomerId     INTEGER NOT NULL REFERENCES Customer(CustomerId)
);

-- -----------------------------------------------------------------------------
-- OrderLine
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS OrderLine (
    OrderLineId INTEGER PRIMARY KEY AUTOINCREMENT,
    Quantity      INTEGER NOT NULL CHECK (Quantity > 0),
    UnitPrice    REAL    NOT NULL CHECK (UnitPrice > 0),
    Discount      REAL    NOT NULL CHECK (Discount >= 0 AND Discount < 1),
    OrderId      INTEGER NOT NULL REFERENCES OrderHeader(OrderId),
    ProductId    INTEGER NOT NULL REFERENCES Product(ProductId)
);

-- -----------------------------------------------------------------------------
-- Indexes for common join / filter columns
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_order_header_customer ON OrderHeader(CustomerId);
CREATE INDEX IF NOT EXISTS idx_order_header_date     ON OrderHeader(OrderDate);
CREATE INDEX IF NOT EXISTS idx_order_line_order      ON OrderLine(OrderId);
CREATE INDEX IF NOT EXISTS idx_order_line_product    ON OrderLine(ProductId);
CREATE INDEX IF NOT EXISTS idx_product_category      ON Product(CategoryId);
CREATE INDEX IF NOT EXISTS idx_product_supplier      ON Product(SupplierId);
