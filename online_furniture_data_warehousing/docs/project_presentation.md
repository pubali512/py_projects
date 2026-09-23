# Online Furniture Data Warehouse — Presentation

> **Format:** 10 min presentation + 5-10 min Q&A  
> **Course:** Datenbanken – Wirtschaftspraktikum

---

## Slide 1 — Title

> **[TODO]** Fill in: project name / CI branding, team members, presentation date.

---

## Slide 2 — Business Context & Constraints

### Problem

- The operational shop DB is optimized for **transactions** ("What is in order #41725?"),
  not analytics.
- Cannot efficiently answer: *"How did revenue per product category develop over 2 years?"*
- Running analytics on the live system **blocks operational traffic**.
- **Solution:** Build a Data Warehouse that separates analytical workloads from the transactional system.

### Constraints & Boundary Conditions

| Constraint | Detail |
|---|---|
| 1 product → exactly 1 supplier | No multi-sourcing; every product has a fixed supplier |
| 1 product → exactly 1 sub-category | Two-level hierarchy (top-category → sub-category) only |
| 1 order header → 1 customer | Orders are not shared between customers |
| 1 order line → 1 product | No product bundling on line level |
| Observation window | 2024-01-01 – 2025-12-31 (two full years) |
| German market only | PLZ-based regional segmentation required for Q2 |
| No production data | Synthetic data generated with Faker + real PLZ mapping from OpenPLZ API |

---

## Slide 3 — Business DB Design (ER)

**Visual:** `[TO ADD — ER Diagram image]`

### Key Points

- **6 entities in 3rd Normal Form (3NF)**
- Entities: `Customer`, `OrderHeader`, `OrderLine`, `Product`, `Category`, `Supplier`
- `Category` is **self-referencing** (parent → child, max 2 levels)
- All primary keys are surrogate integers (`AUTOINCREMENT`)
- Referential integrity enforced with FK constraints (`PRAGMA foreign_keys = ON`)

### Data Volume

| Entity | Rows |
|---|---|
| Supplier | 20 (10 Germany + 10 neighbouring countries) |
| Category | 15 (5 top-level + 10 sub-categories) |
| Product | 120 |
| Customer | 5,000 |
| OrderHeader | 30,000 |
| OrderLine | ~85,500 (~2.85 lines/order) |

---

## Slide 4 — DWH Conceptual Design (mER)

**Visual:** `[TO ADD — mER Diagram image]`

### Key Points

- Central **fact: Sales** with measures: Quantity, GrossAmount, DiscountAmount, NetAmount, ShippingCost
- **4 classification dimensions** with roll-up hierarchies:

| Dimension | Hierarchy (fine → coarse) |
|---|---|
| **Date** | Day → Week → Year; Day → Month → Quarter → Year |
| **Customer** | Customer → PostalCode → PLZZone → PLZRegion → *Top*; PostalCode → City → FederalState → *Top* |
| **Product** | Product → CategoryName → TopCategoryName → *Top* |
| **Supplier** | Supplier → City → Country → *Top* |

- Arrows show the **roll-up direction** (fine → coarse granularity)
- Each dimension chain ends at an implicit **Top** level

---

## Slide 5 — DWH Logical Design (Star Schema)

### Fact Table Grain

> **One row per order line** (most granular measurable event)

### Schema

```
         DIM_Date          DIM_Customer
              |                 |
         [DateSk]          [CustomerSk]
              |                 |
DIM_Supplier--+---FACT_Sales----+--DIM_Product
         [SupplierSk]      [ProductSk]
```

### FACT_Sales Measures

| Column | Derivation |
|---|---|
| `OrderId` | Degenerate dimension (no separate dim table needed) |
| `Quantity` | Direct from OrderLine |
| `GrossAmount` | Quantity × UnitPrice |
| `DiscountAmount` | GrossAmount × Discount |
| `NetAmount` | GrossAmount − DiscountAmount |
| `ShippingCost` | Direct from OrderHeader |

### Dimension Row Counts

| Table | Rows | SCD |
|---|---|---|
| DIM_Date | 731 (every date in 2024–2025) | 0 |
| DIM_Customer | 5,000 | 2 |
| DIM_Product | 120 | 1 |
| DIM_Supplier | 20 | 0 |
| **FACT_Sales** | **~85,500** | — |

### PLZ Hierarchy in DIM_Customer

| Column | Derivation | Cardinality |
|---|---|---|
| `PlzRegion` | First digit of PostalCode (0–9) | 10 |
| `PlzZone` | First two digits | ~83 |
| `City` | From PLZ mapping CSV | 75 |
| `FederalState` | From PLZ mapping CSV | 16 |

---

## Slide 6 — Slowly Changing Dimensions (SCD)

| Dimension | SCD Type | Changed Attributes | Justification |
|---|---|---|---|
| `DIM_Date` | **0** — Keep original | — | Dates are immutable |
| `DIM_Supplier` | **0** — Keep original | — | Supplier identity assumed stable |
| `DIM_Product` | **1** — Overwrite | ProductName, ListPrice, Colour, Material | Corrections tolerated; no analytical query requires the old product values |
| `DIM_Customer` | **2** — Expire + Insert | PostalCode, StreetAddress, City, FederalState, PlzRegion, PlzZone | Customer relocation changes PLZ region → historical orders must stay attributed to the old region for Q2 (regional analysis) |

### SCD 2 Implementation (DIM_Customer)

| Column | Type | Meaning |
|---|---|---|
| `ValidFrom` | DATE | Start of validity (= CustomerSince for first load) |
| `ValidTo` | DATE | End of validity (NULL = currently active) |
| `IsCurrent` | INTEGER (0/1) | 1 = active row |

**ETL logic:**
```
IF customer not in DIM_Customer:
    INSERT (ValidFrom=CustomerSince, ValidTo=NULL, IsCurrent=1)

ELSE IF PostalCode OR StreetAddress changed:
    UPDATE old row → ValidTo=today, IsCurrent=0
    INSERT new row → ValidFrom=today, ValidTo=NULL, IsCurrent=1

ELSE:
    skip
```

---

## Slide 7 — Implementation Details

### ETL Pipeline (3 Stages)

```
Business DB       Stage 1: Extract          Stage 2: Transform         Stage 3: Load
(source tables) → RAW_ staging tables  →  FULL_ staging tables  →  DIM_* + FACT_Sales
                  etl_extract.py           etl_transform.py            etl_dim_*.py
                                           sql/transform/*.sql         etl_fact_sales.py
```

| Stage | Purpose | Key transformations |
|---|---|---|
| **RAW_** | Direct copy from source | None — raw snapshot |
| **FULL_** | Cleansed & enriched | PLZ region/zone derivation, category hierarchy flattening, GrossAmount/DiscountAmount/NetAmount computation |
| **DIM_ / FACT_** | Target DWH | Surrogate key assignment, SCD logic, FK resolution |

### Data Generation

- **Python + Faker** (`de_DE` locale) for names, emails, streets
- **Real PLZ data** via [OpenPLZ API](https://openplzapi.org/) — 1,150 PLZ codes across 75 German cities (all 16 federal states)
- Faker's built-in `de_DE` locale does **NOT** match PLZ ↔ city correctly → curated CSV solves this
- Seeded random generator (`SEED = 42`) → fully reproducible data sets

### Orchestration

- Single CLI entry point: **`python python/run.py`**
  - Option 1: Generate Business DB (Faker)
  - Option 2: Generate demo delta (incremental data + SCD 2 address changes)
  - Option 3: Run ETL pipeline
  - Option 4: Execute analytical queries interactively
- Full pipeline: **`run_all_etl.py`** (Extract → Transform → DimDate → DimSupplier → DimProduct → DimCustomer → FactSales)
- All ETL steps are **idempotent** — safe to re-run without duplicates

### Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.14 |
| Database | SQLite (portable, no server) |
| Data generation | Faker + OpenPLZ API |
| SQL | Standard SQL (SQLite dialect) |

---

## Slide 8 — Analytical Questions

| ID | Question | Dimensions |
|---|---|---|
| **Q1** | How does net revenue as well as Discounts develop per top-level product category and Quarter? | DIM_Date, DIM_Product |
| **Q2** | Which 10 postal code zones (first 2 digits of PLZ) generate the maximum net revenue? | DIM_Customer |
| **Q3** | What are the two highest net revenue generating product categories per federal state? | DIM_Customer, DIM_Product |
| **Q4** | Which weekdays see the highest order volume across the two-year period? | DIM_Date |
| **Q5** | Which calendar weeks see the highest order volume? (Top 10) | DIM_Date |
| **Q6** | How does revenue compare across Budget / Mid-range / Premium product price segments? | DIM_Product |
| **Q7** | Which federal states show the strongest revenue growth from 2024 to 2025? | DIM_Customer, DIM_Date |
| **Q8** | Which 3 suppliers generate the most net revenue per Quarter? | DIM_Supplier, DIM_Date |
| **Q9** | Which suppliers’ products carry the highest average Discount rate, and does it correlate with order volume? | DIM_Supplier |

**Mandatory for submission:** Q1, Q2, Q3.

> **[TODO]** Add sample query result screenshots / key numbers once DB is regenerated.

---

## Slide 9 — Lessons Learned

> **[TODO]** Fill in before the presentation:

### Highlights

- [ ] *What went particularly well?*

### Problems + Solutions

| Problem | How it was solved |
|---|---|
| Faker `de_DE` locale generates incorrect PLZ ↔ city pairs | Fetched real PLZ codes from OpenPLZ API; stored 1,150 PLZ–city–state mappings in a curated CSV |
| *[TODO: add your own problems here]* | *[TODO]* |

### Advice to Colleagues

- Always validate that your test data generator produces **geographically correct** attribute combinations — incorrect synthetic data can hide bugs in regional analysis queries.
- *[TODO: add your own advice here]*
