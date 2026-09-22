# Project Documentation — Online Furniture Data Warehouse

---

## 1. Business DB (Source System)

### 1.1 Entity-Relationship Diagram

```mermaid
erDiagram
    Supplier {
        int SupplierId PK
        string SupplierName
        string City
        string Country
    }
    Category {
        int CategoryId PK
        string CategoryName
        int ParentCategoryId FK
    }
    Product {
        int ProductId PK
        string ProductName
        float ListPrice
        string Colour
        string Material
        int CategoryId FK
        int SupplierId FK
    }
    Customer {
        int CustomerId PK
        string FirstName
        string LastName
        string Email
        string StreetAddress
        string PostalCode
        string City
        string FederalState
        date CustomerSince
    }
    OrderHeader {
        int OrderId PK
        date OrderDate
        string PaymentMethod
        float ShippingCost
        int CustomerId FK
    }
    OrderLine {
        int OrderLineId PK
        int Quantity
        float UnitPrice
        float Discount
        int OrderId FK
        int ProductId FK
    }

    Supplier    ||--o{ Product      : "supplies"
    Category    ||--o{ Product      : "categorizes"
    Category    ||--o{ Category     : "parent of"
    Customer    ||--o{ OrderHeader : "places"
    OrderHeader ||--o{ OrderLine  : "contains"
    Product     ||--o{ OrderLine   : "ordered in"
```

### 1.2 Relational Schema

```
Supplier(SupplierId PK, SupplierName, City, Country)

Category(CategoryId PK, CategoryName,
         ParentCategoryId FK → Category)

Product(ProductId PK, ProductName, ListPrice, Colour, Material,
        CategoryId FK → Category, SupplierId FK → Supplier)

Customer(CustomerId PK, FirstName, LastName, Email, StreetAddress,
         PostalCode, City, FederalState, CustomerSince)

OrderHeader(OrderId PK, OrderDate, PaymentMethod, ShippingCost,
             CustomerId FK → Customer)

OrderLine(OrderLineId PK, Quantity, UnitPrice, Discount,
           OrderId FK → OrderHeader, ProductId FK → Product)
```

### 1.3 Normal Form Verification

| Form | Check | Result |
|---|---|---|
| **1NF** | Atomic attributes, no repeating groups, single-column PKs | ✅ |
| **2NF** | No partial dependencies (all PKs are surrogates — no composite PK) | ✅ |
| **3NF** | `PostalCode → City`? No — City stored independently. `UnitPrice ≠ ListPrice` (dynamic pricing). Category attributes separated. | ✅ |

All 6 tables in **3NF**.

### 1.4 Synthetic Data Generation

| Entity | Count | Method |
|---|---|---|
| Supplier | 20 | Hardcoded (10 Germany, 10 neighboring countries) |
| Category | 15 | 5 top-level + 10 sub-categories (hardcoded tree) |
| Product | 120 | Templates × adjectives; price €50–€2,500 random |
| Customer | 5,000 | Faker `de_DE`; Email derived from name; PLZ/City from curated CSV |
| OrderHeader | 30,000 | Random dates 2024-01-01 to 2025-12-31; weighted payment methods |
| OrderLine | ~85,500 | 1–5 lines/order; UnitPrice = ListPrice ±10%; 80% zero Discount |

PLZ accuracy: 1,150 real German postal codes for 75 cities from OpenPLZ API — stored in `data/plz_city_mapping.csv`. Faker's `de_DE` locale does NOT match PLZ ↔ City correctly; curated CSV solves this.

---

## 2. Data Warehouse (Star Schema)

### 2.1 Conceptual Design (mER Diagram)

The mER (multidimensional ER) diagram shows the **conceptual DWH schema**: the central fact table with its measures and the four classification hierarchies. Arrows indicate the roll-up direction (fine → coarse); each chain ends at an implicit **Top** level.

```mermaid
flowchart TB
    classDef topLevel fill:#fff,stroke:#555,stroke-dasharray:5 5,font-style:italic
    classDef factNode  fill:#e8e8e8,stroke:#000,stroke-width:3px

    %% ── Fact table ──────────────────────────────────────────────────────────
    FACT["Sales\n────────────────────────\nQuantity\nGross Amount\nDiscount Amount\nNet Amount\nShipping Cost"]:::factNode

    %% ── Date dimension ──────────────────────────────────────────────────────
    ZDay[Day]
    ZWeek[Week]
    ZMonth[Month]
    ZQuarter[Quarter]
    ZYear[Year]
    ZTop([Top]):::topLevel

    ZDay --> ZWeek --> ZYear
    ZDay --> ZMonth --> ZQuarter --> ZYear --> ZTop

    %% ── Customer dimension ──────────────────────────────────────────────────
    KCustomer[Customer]
    KPostalCode[Postal Code]
    KPLZZone[PLZ Zone]
    KPLZReg[PLZ Region]
    KCity[City]
    KState[Federal State]
    KTop([Top]):::topLevel

    KCustomer --> KPostalCode --> KPLZZone --> KPLZReg --> KTop
    KPostalCode --> KCity --> KState --> KTop

    %% ── Product dimension ───────────────────────────────────────────────────
    PProduct[Product]
    PSubCat[Sub-Category]
    PTopCat[Top-Category]
    PTop([Top]):::topLevel

    PProduct --> PSubCat --> PTopCat --> PTop

    %% ── Supplier dimension ──────────────────────────────────────────────────
    LSupplier[Supplier]
    LCity[City]
    LCountry[Country]
    LTop([Top]):::topLevel

    LSupplier --> LCity --> LCountry --> LTop

    %% ── Connections: fact → base dimension levels ────────────────────────────
    FACT --- ZDay
    FACT --- KCustomer
    FACT --- PProduct
    FACT --- LSupplier
```

### 2.2 Star Schema Diagram

```mermaid
erDiagram
    DIM_Date {
        int DateSk PK
        date FullDate
        int Day
        int Month
        string MonthName
        int Quarter
        int Year
        int Weekday
        string WeekdayName
        int CalendarWeek
    }
    DIM_Customer {
        int CustomerSk PK
        int CustomerId
        string FirstName
        string LastName
        string Email
        string PostalCode
        string PlzRegion
        string PlzZone
        string City
        string FederalState
        date ValidFrom
        date ValidTo
        int IsCurrent
    }
    DIM_Product {
        int ProductSk PK
        int ProductId
        string ProductName
        string Colour
        string Material
        float ListPrice
        string CategoryName
        string TopCategoryName
    }
    DIM_Supplier {
        int SupplierSk PK
        int SupplierId
        string SupplierName
        string City
        string Country
    }
    FACT_Sales {
        int SalesSk PK
        int DateSk FK
        int CustomerSk FK
        int ProductSk FK
        int SupplierSk FK
        int OrderId
        int Quantity
        float GrossAmount
        float DiscountAmount
        float NetAmount
        float ShippingCost
    }

    DIM_Date     ||--o{ FACT_Sales : "DateSk"
    DIM_Customer ||--o{ FACT_Sales : "CustomerSk"
    DIM_Product  ||--o{ FACT_Sales : "ProductSk"
    DIM_Supplier ||--o{ FACT_Sales : "SupplierSk"
```

### 2.3 Grain and Row Counts

Grain: **one row per order line**.

| Table | Rows |
|---|---|
| DIM_Date | 731 (every date in 2024–2025) |
| DIM_Customer | 5,000 |
| DIM_Product | 120 |
| DIM_Supplier | 20 |
| FACT_Sales | ~85,500 |

### 2.4 PLZ Hierarchy in DIM_Customer

| Column | Derivation | Cardinality | Used in |
|---|---|---|---|
| PlzRegion | `PostalCode[0]` | 10 (0–9) | Q2, Q6 |
| PlzZone | `PostalCode[:2]` | ~83 | drill-down |
| City | from PLZ mapping CSV | 75 | display |
| FederalState | from PLZ mapping CSV | 16 | Q6 |

---

## 3. SCD Analysis

| Dimension | SCD Type | Changed attributes | Justification |
|---|---|---|---|
| DIM_Date | 0 | — | Dates immutable |
| DIM_Supplier | 0 | — | Supplier identity stable |
| DIM_Product | 1 (overwrite) | ProductName, ListPrice, Colour, Material | Corrections tolerated; no historical query requires old values |
| DIM_Customer | **2** (expire + insert) | PostalCode, StreetAddress, City, FederalState, PlzRegion, PlzZone | Relocation changes region → historical order assignment matters for Q2/Q6 |

### SCD 2 tracking columns (DIM_Customer)

| Column | Type | Description |
|---|---|---|
| ValidFrom | DATE | Row start date (CustomerSince for first load; ETL date on change) |
| ValidTo | DATE | Row end date (NULL = active) |
| IsCurrent | INTEGER | 1 = active; 0 = historical |

### SCD 2 ETL logic

```
IF Customer not in DIM_Customer:
    INSERT (ValidFrom=CustomerSince, ValidTo=NULL, IsCurrent=1)

ELSE IF PostalCode OR StreetAddress changed:
    UPDATE current row: ValidTo=today, IsCurrent=0
    INSERT new row: ValidFrom=today, ValidTo=NULL, IsCurrent=1

ELSE:
    skip
```

### MSSQL ALTER equivalent (for schema migration reference)

```sql
ALTER TABLE DIM_Customer ADD ValidFrom  DATE  NOT NULL DEFAULT GETDATE();
ALTER TABLE DIM_Customer ADD ValidTo    DATE  NULL;
ALTER TABLE DIM_Customer ADD IsCurrent  BIT   NOT NULL DEFAULT 1;
```

---

## 4. ETL Pipeline

### 4.1 Pipeline Stages

```
Business DB          Stage 1            Stage 2            DWH
(source tables)  →  RAW_ staging   →  FULL_ staging  →  dim_* / fact_*
                   etl_extract.py    etl_transform.py   etl_dim_*.py
                                     sql/transform/     etl_fact_sales.py
```

### 4.2 Stage 1 — Extract (RAW_)

Direct copy from source. No transformation.

| Source | RAW_ table |
|---|---|
| Customer | RAW_BusinessDB_Customer |
| OrderHeader | RAW_BusinessDB_OrderHeader |
| OrderLine | RAW_BusinessDB_OrderLine |
| Product | RAW_BusinessDB_Product |
| Category | RAW_BusinessDB_Category |
| Supplier | RAW_BusinessDB_Supplier |

### 4.3 Stage 2 — Transform (FULL_)

SQL scripts in `sql/transform/`.

| FULL_ table | SQL file | Key transformation |
|---|---|---|
| FULL_BusinessDB_DWH_Customer | 01_FULL_customer.sql | Derive PlzRegion, PlzZone from PostalCode |
| FULL_BusinessDB_DWH_Product | 02_FULL_product.sql | JOIN Category → sub-Category name + top-Category name |
| FULL_BusinessDB_DWH_Sales | 03_FULL_sales.sql | Compute gross, DiscountAmount, NetAmount |

### 4.4 Stage 3 — Load (DWH)

| DWH table | Source | SCD | ETL module |
|---|---|---|---|
| DIM_Date | RAW_OrderHeader.OrderDate | 0 | etl_dim_date.py |
| DIM_Supplier | RAW_Supplier | 0 | etl_dim_supplier.py |
| DIM_Product | RAW_Product + Category join | 1 | etl_dim_product.py |
| DIM_Customer | RAW_Customer + PLZ derivation | 2 | etl_dim_customer.py |
| FACT_Sales | RAW_OrderLine + header + Product | — | etl_fact_sales.py |

### 4.5 FACT_Sales Column Mapping

| Target | Source | Transform |
|---|---|---|
| DateSk | OrderHeader.OrderDate | `int(date.replace('-',''))` |
| CustomerSk | DIM_Customer.CustomerId (IsCurrent=1) | SK lookup |
| ProductSk | DIM_Product.ProductId | SK lookup |
| SupplierSk | DIM_Supplier.SupplierId | SK lookup |
| OrderId | OrderHeader.OrderId | Degenerate dimension |
| Quantity | OrderLine.Quantity | Direct |
| GrossAmount | Quantity × UnitPrice | FULL_Sales |
| DiscountAmount | gross × Discount | FULL_Sales |
| NetAmount | gross − Discount | FULL_Sales |
| ShippingCost | OrderHeader.ShippingCost | Direct |

---

## 5. Storage Calculation

### Business DB

| Table | Rows | Avg row (bytes) | Estimated |
|---|---|---|---|
| Supplier | 20 | 80 | 1.6 KB |
| Category | 15 | 60 | 0.9 KB |
| Product | 120 | 120 | 14.4 KB |
| Customer | 5,000 | 250 | 1.2 MB |
| OrderHeader | 30,000 | 100 | 2.9 MB |
| OrderLine | 85,500 | 60 | 4.9 MB |
| **Subtotal** | | | **~9.0 MB** |

With SQLite overhead (B-tree, indexes, pages): **~11–12 MB**.

### DWH + Staging (additional)

| Layer | Approx. |
|---|---|
| DWH dimensions + FACT_Sales | ~8 MB |
| RAW_ + FULL_ staging | ~12 MB |
| **Total combined DB** | **~30–35 MB** |

---

## 6. Analytical Questions

All SQL in `sql/analytics/`. Run via `python python/run.py` → option 4.

| ID | Question | Dimensions |
|---|---|---|
| Q1 | Revenue and Discount per Category and Quarter | DIM_Date, DIM_Product |
| Q2a | Average order value by PLZ region | DIM_Customer |
| Q2b | Category mix by PLZ region | DIM_Customer, DIM_Product |
| Q3a | Peak order volume by Weekday | DIM_Date |
| Q3b | Top 10 peak calendar weeks | DIM_Date |
| Q4 | Discount effectiveness vs. Quantity and revenue | FACT_Sales |
| Q5 | Revenue by price segment (Budget/Mid/Premium) | DIM_Product |
| Q6 | Federal state revenue growth 2024→2025 | DIM_Customer, DIM_Date |
| Q7 | Supplier revenue by Quarter and share | DIM_Supplier, DIM_Date |
| Q8 | Supplier Discount rate vs. order volume | DIM_Supplier |

**Mandatory for submission:** Q1, Q2 (covers Q2a + Q2b).

**Supplier-specific (extends DIM_Supplier):** Q7, Q8.
