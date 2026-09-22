# Project Documentation — Online Furniture Data Warehouse

---

## 1. Business DB (Source System)

### 1.1 Entity-Relationship Diagram

```mermaid
erDiagram
    supplier {
        int supplier_id PK
        string supplier_name
        string city
        string country
    }
    category {
        int category_id PK
        string category_name
        int parent_category_id FK
    }
    product {
        int product_id PK
        string product_name
        float list_price
        string colour
        string material
        int category_id FK
        int supplier_id FK
    }
    customer {
        int customer_id PK
        string first_name
        string last_name
        string email
        string street_address
        string postal_code
        string city
        string federal_state
        date customer_since
    }
    order_header {
        int order_id PK
        date order_date
        string payment_method
        float shipping_cost
        int customer_id FK
    }
    order_line {
        int order_line_id PK
        int quantity
        float unit_price
        float discount
        int order_id FK
        int product_id FK
    }

    supplier    ||--o{ product      : "supplies"
    category    ||--o{ product      : "categorizes"
    category    ||--o{ category     : "parent of"
    customer    ||--o{ order_header : "places"
    order_header ||--o{ order_line  : "contains"
    product     ||--o{ order_line   : "ordered in"
```

### 1.2 Relational Schema

```
supplier(supplier_id PK, supplier_name, city, country)

category(category_id PK, category_name,
         parent_category_id FK → category)

product(product_id PK, product_name, list_price, colour, material,
        category_id FK → category, supplier_id FK → supplier)

customer(customer_id PK, first_name, last_name, email, street_address,
         postal_code, city, federal_state, customer_since)

order_header(order_id PK, order_date, payment_method, shipping_cost,
             customer_id FK → customer)

order_line(order_line_id PK, quantity, unit_price, discount,
           order_id FK → order_header, product_id FK → product)
```

### 1.3 Normal Form Verification

| Form | Check | Result |
|---|---|---|
| **1NF** | Atomic attributes, no repeating groups, single-column PKs | ✅ |
| **2NF** | No partial dependencies (all PKs are surrogates — no composite PK) | ✅ |
| **3NF** | `postal_code → city`? No — city stored independently. `unit_price ≠ list_price` (dynamic pricing). Category attributes separated. | ✅ |

All 6 tables in **3NF**.

### 1.4 Synthetic Data Generation

| Entity | Count | Method |
|---|---|---|
| supplier | 20 | Hardcoded (10 Germany, 10 neighboring countries) |
| category | 15 | 5 top-level + 10 sub-categories (hardcoded tree) |
| product | 120 | Templates × adjectives; price €50–€2,500 random |
| customer | 5,000 | Faker `de_DE`; email derived from name; PLZ/city from curated CSV |
| order_header | 30,000 | Random dates 2024-01-01 to 2025-12-31; weighted payment methods |
| order_line | ~85,500 | 1–5 lines/order; unit_price = list_price ±10%; 80% zero discount |

PLZ accuracy: 1,150 real German postal codes for 75 cities from OpenPLZ API — stored in `data/plz_city_mapping.csv`. Faker's `de_DE` locale does NOT match PLZ ↔ city correctly; curated CSV solves this.

---

## 2. Data Warehouse (Star Schema)

### 2.1 Schema Diagram

```mermaid
erDiagram
    dim_date {
        int date_sk PK
        date full_date
        int day
        int month
        string month_name
        int quarter
        int year
        int weekday
        string weekday_name
        int calendar_week
    }
    dim_customer {
        int customer_sk PK
        int customer_id
        string first_name
        string last_name
        string email
        string postal_code
        string plz_region
        string plz_zone
        string city
        string federal_state
        date valid_from
        date valid_to
        int is_current
    }
    dim_product {
        int product_sk PK
        int product_id
        string product_name
        string colour
        string material
        float list_price
        string category_name
        string top_category_name
    }
    dim_supplier {
        int supplier_sk PK
        int supplier_id
        string supplier_name
        string city
        string country
    }
    fact_sales {
        int sales_sk PK
        int date_sk FK
        int customer_sk FK
        int product_sk FK
        int supplier_sk FK
        int order_id
        int quantity
        float gross_amount
        float discount_amount
        float net_amount
        float shipping_cost
    }

    dim_date     ||--o{ fact_sales : "date_sk"
    dim_customer ||--o{ fact_sales : "customer_sk"
    dim_product  ||--o{ fact_sales : "product_sk"
    dim_supplier ||--o{ fact_sales : "supplier_sk"
```

### 2.2 Grain and Row Counts

Grain: **one row per order line**.

| Table | Rows |
|---|---|
| dim_date | 731 (every date in 2024–2025) |
| dim_customer | 5,000 |
| dim_product | 120 |
| dim_supplier | 20 |
| fact_sales | ~85,500 |

### 2.3 PLZ Hierarchy in dim_customer

| Column | Derivation | Cardinality | Used in |
|---|---|---|---|
| plz_region | `postal_code[0]` | 10 (0–9) | Q2, Q6 |
| plz_zone | `postal_code[:2]` | ~83 | drill-down |
| city | from PLZ mapping CSV | 75 | display |
| federal_state | from PLZ mapping CSV | 16 | Q6 |

---

## 3. SCD Analysis

| Dimension | SCD Type | Changed attributes | Justification |
|---|---|---|---|
| dim_date | 0 | — | Dates immutable |
| dim_supplier | 0 | — | Supplier identity stable |
| dim_product | 1 (overwrite) | product_name, list_price, colour, material | Corrections tolerated; no historical query requires old values |
| dim_customer | **2** (expire + insert) | postal_code, street_address, city, federal_state, plz_region, plz_zone | Relocation changes region → historical order assignment matters for Q2/Q6 |

### SCD 2 tracking columns (dim_customer)

| Column | Type | Description |
|---|---|---|
| valid_from | DATE | Row start date (customer_since for first load; ETL date on change) |
| valid_to | DATE | Row end date (NULL = active) |
| is_current | INTEGER | 1 = active; 0 = historical |

### SCD 2 ETL logic

```
IF customer not in dim_customer:
    INSERT (valid_from=customer_since, valid_to=NULL, is_current=1)

ELSE IF postal_code OR street_address changed:
    UPDATE current row: valid_to=today, is_current=0
    INSERT new row: valid_from=today, valid_to=NULL, is_current=1

ELSE:
    skip
```

### MSSQL ALTER equivalent (for schema migration reference)

```sql
ALTER TABLE dim_customer ADD valid_from  DATE  NOT NULL DEFAULT GETDATE();
ALTER TABLE dim_customer ADD valid_to    DATE  NULL;
ALTER TABLE dim_customer ADD is_current  BIT   NOT NULL DEFAULT 1;
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
| customer | RAW_BusinessDB_Customer |
| order_header | RAW_BusinessDB_OrderHeader |
| order_line | RAW_BusinessDB_OrderLine |
| product | RAW_BusinessDB_Product |
| category | RAW_BusinessDB_Category |
| supplier | RAW_BusinessDB_Supplier |

### 4.3 Stage 2 — Transform (FULL_)

SQL scripts in `sql/transform/`.

| FULL_ table | SQL file | Key transformation |
|---|---|---|
| FULL_BusinessDB_DWH_Customer | 01_FULL_customer.sql | Derive plz_region, plz_zone from postal_code |
| FULL_BusinessDB_DWH_Product | 02_FULL_product.sql | JOIN category → sub-category name + top-category name |
| FULL_BusinessDB_DWH_Sales | 03_FULL_sales.sql | Compute gross, discount_amount, net_amount |

### 4.4 Stage 3 — Load (DWH)

| DWH table | Source | SCD | ETL module |
|---|---|---|---|
| dim_date | RAW_OrderHeader.order_date | 0 | etl_dim_date.py |
| dim_supplier | RAW_Supplier | 0 | etl_dim_supplier.py |
| dim_product | RAW_Product + category join | 1 | etl_dim_product.py |
| dim_customer | RAW_Customer + PLZ derivation | 2 | etl_dim_customer.py |
| fact_sales | RAW_OrderLine + header + product | — | etl_fact_sales.py |

### 4.5 fact_sales Column Mapping

| Target | Source | Transform |
|---|---|---|
| date_sk | order_header.order_date | `int(date.replace('-',''))` |
| customer_sk | dim_customer.customer_id (is_current=1) | SK lookup |
| product_sk | dim_product.product_id | SK lookup |
| supplier_sk | dim_supplier.supplier_id | SK lookup |
| order_id | order_header.order_id | Degenerate dimension |
| quantity | order_line.quantity | Direct |
| gross_amount | quantity × unit_price | FULL_Sales |
| discount_amount | gross × discount | FULL_Sales |
| net_amount | gross − discount | FULL_Sales |
| shipping_cost | order_header.shipping_cost | Direct |

---

## 5. Storage Calculation

### Business DB

| Table | Rows | Avg row (bytes) | Estimated |
|---|---|---|---|
| supplier | 20 | 80 | 1.6 KB |
| category | 15 | 60 | 0.9 KB |
| product | 120 | 120 | 14.4 KB |
| customer | 5,000 | 250 | 1.2 MB |
| order_header | 30,000 | 100 | 2.9 MB |
| order_line | 85,500 | 60 | 4.9 MB |
| **Subtotal** | | | **~9.0 MB** |

With SQLite overhead (B-tree, indexes, pages): **~11–12 MB**.

### DWH + Staging (additional)

| Layer | Approx. |
|---|---|
| DWH dimensions + fact_sales | ~8 MB |
| RAW_ + FULL_ staging | ~12 MB |
| **Total combined DB** | **~30–35 MB** |

---

## 6. Analytical Questions

All SQL in `sql/analytics/`. Run via `python python/run.py` → option 4.

| ID | Question | Dimensions |
|---|---|---|
| Q1 | Revenue and discount per category and quarter | dim_date, dim_product |
| Q2a | Average order value by PLZ region | dim_customer |
| Q2b | Category mix by PLZ region | dim_customer, dim_product |
| Q3a | Peak order volume by weekday | dim_date |
| Q3b | Top 10 peak calendar weeks | dim_date |
| Q4 | Discount effectiveness vs. quantity and revenue | fact_sales |
| Q5 | Revenue by price segment (Budget/Mid/Premium) | dim_product |
| Q6 | Federal state revenue growth 2024→2025 | dim_customer, dim_date |
| Q7 | Supplier revenue by quarter and share | dim_supplier, dim_date |
| Q8 | Supplier discount rate vs. order volume | dim_supplier |

**Mandatory for submission:** Q1, Q2 (covers Q2a + Q2b).

**Supplier-specific (extends dim_supplier):** Q7, Q8.
