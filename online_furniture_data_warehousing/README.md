# Online Furniture Data Warehouse

A small but complete data warehouse for a German online furniture retailer.
Built with Python 3.10+ and SQLite.

---

## Project Overview

| Layer | Technology |
|---|---|
| Operational DB (Business DB) | SQLite — 6 tables in 3NF |
| Data Warehouse | SQLite — star schema (4 dimensions + 1 fact table) |
| Data generation | Python + Faker (`data_gen/generate_data.py`) |
| ETL | Python — modular, one file per dimension/fact (`etl/`) |
| CLI front-end | `python/run.py` — interactive menu |

---

## Quick Start

All commands are run from the **project root** directory.

### Step 0 — Install dependencies (once)

```bash
pip install faker
```

### Step 1 — Prepare the PLZ-city mapping (once)

Fetches real German postal codes for 75 cities from the OpenPLZ API
and writes `data/plz_city_mapping.csv`.

> Skip this step if `data/plz_city_mapping.csv` already exists.

```bash
python python/data_gen/prepare_plz_data.py
```

### Step 2 — Generate Business DB data

Generates synthetic data (~5,000 customers, ~30,000 orders, ~85,000 order lines)
and writes `data/furniture.db`.

```bash
python python/data_gen/generate_data.py
```

### Step 3 — Run the ETL pipeline

Creates the DWH star schema and loads all dimension and fact tables.

```bash
python python/etl/run_all_etl.py
```

---

## Interactive CLI

Steps 2 and 3 can also be run together via the interactive command-line front-end:

```bash
python python/run.py
```

The menu offers:
1. **Load and transform the database** — runs data generation + ETL in one step
2. **Execute an analytical query** — choose from 10 predefined queries (Q1–Q6, Q-S1, Q-S2)

---

## Project Structure

```
online_furniture_data_warehousing/
├── data/
│   ├── furniture.db                   # SQLite database (created at runtime)
│   └── plz_city_mapping.csv           # PLZ ↔ city ↔ federal_state mapping
│
├── sql/
│   ├── 01_create_business_db.sql      # Business DB DDL (6 tables, 3NF)
│   ├── 02_create_dwh.sql              # DWH DDL (star schema + staging tables)
│   ├── 03_alter_scd.sql               # SCD analysis + MSSQL ALTER equivalents
│   └── 04_analytical_queries.sql      # All 10 analytical queries
│
├── python/
│   ├── db.py                          # DB connection abstraction
│   ├── run.py                         # Interactive CLI front-end
│   ├── data_gen/
│   │   ├── prepare_plz_data.py        # One-time PLZ data fetch
│   │   └── generate_data.py           # Synthetic data generation
│   └── etl/
│       ├── etl_extract.py             # Extract source → RAW_ staging
│       ├── etl_dim_date.py            # Load dim_date
│       ├── etl_dim_supplier.py        # Load dim_supplier
│       ├── etl_dim_product.py         # Load dim_product (SCD1)
│       ├── etl_dim_customer.py        # Load dim_customer (SCD2)
│       ├── etl_fact_sales.py          # Load fact_sales
│       └── run_all_etl.py             # ETL orchestrator
│
└── docs/                              # Documentation (to be added)
```

---

## Analytical Questions

| ID | Question | Dimensions |
|---|---|---|
| Q1 | Revenue and discount by category and quarter | dim_date, dim_product |
| Q2a | Average order value by PLZ region | dim_customer |
| Q2b | Category mix by PLZ region | dim_customer, dim_product |
| Q3a | Peak order volume by weekday | dim_date |
| Q3b | Peak calendar weeks | dim_date |
| Q4 | Discount effectiveness vs. quantity | fact_sales |
| Q5 | Revenue by price segment | dim_product |
| Q6 | Federal state revenue growth 2024→2025 | dim_customer, dim_date |
| Q-S1 | Supplier revenue by quarter | dim_supplier, dim_date |
| Q-S2 | Supplier discount rate vs. order volume | dim_supplier |

---

## Switching to a Different Database

The database backend is isolated in `python/db.py`.
To migrate from SQLite to MSSQL (or PostgreSQL), change only that file:

```python
# MSSQL example
import pyodbc
PLACEHOLDER = "%s"
CONN_STRING = "DRIVER={SQL Server};SERVER=...;DATABASE=...;UID=...;PWD=..."

def connect():
    return pyodbc.connect(CONN_STRING)
```

Also update the DDL files (`sql/`) for T-SQL data types and `IDENTITY` instead of `AUTOINCREMENT`.
