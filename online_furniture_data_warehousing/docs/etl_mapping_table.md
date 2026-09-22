# ETL Mapping Table

Pipeline: `python/etl/run_all_etl.py`

Stages: RAW_ → FULL_ → DWH target

---

## Stage 1: Extract (RAW_)

Direct copy from Business DB source tables. No transformation.

| Source table | RAW_ staging table |
|---|---|
| `customer` | `RAW_BusinessDB_Customer` |
| `order_header` | `RAW_BusinessDB_OrderHeader` |
| `order_line` | `RAW_BusinessDB_OrderLine` |
| `product` | `RAW_BusinessDB_Product` |
| `category` | `RAW_BusinessDB_Category` |
| `supplier` | `RAW_BusinessDB_Supplier` |

SQL: `etl_extract.py` / `sql/02_create_dwh.sql` (staging DDL)

---

## Stage 2: Transform (FULL_)

Enrichment and computed columns. SQL in `sql/transform/`.

| FULL_ table | SQL file | Key transformations |
|---|---|---|
| `FULL_BusinessDB_DWH_Customer` | `01_FULL_customer.sql` | `plz_region = substr(postal_code, 1, 1)`, `plz_zone = substr(postal_code, 1, 2)` |
| `FULL_BusinessDB_DWH_Product` | `02_FULL_product.sql` | JOIN category → sub-category + top-category name |
| `FULL_BusinessDB_DWH_Sales` | `03_FULL_sales.sql` | `gross = qty × price`, `discount_amount = gross × discount`, `net = gross − discount` |

---

## Stage 3: Load (DWH target)

| DWH table | Source | SCD | ETL module |
|---|---|---|---|
| `dim_date` | `RAW_BusinessDB_OrderHeader` (order_date) | 0 | `etl_dim_date.py` |
| `dim_supplier` | `RAW_BusinessDB_Supplier` | 0 | `etl_dim_supplier.py` |
| `dim_product` | `FULL_BusinessDB_DWH_Product` (via RAW join) | 1 (overwrite) | `etl_dim_product.py` |
| `dim_customer` | `RAW_BusinessDB_Customer` + FULL derivation | 2 (expire+insert) | `etl_dim_customer.py` |
| `fact_sales` | `RAW_BusinessDB_OrderLine` + header + product | — | `etl_fact_sales.py` |

---

## Column Mapping: fact_sales

| Target column | Source | Transformation |
|---|---|---|
| date_sk | order_header.order_date | `int(date.replace('-',''))` |
| customer_sk | dim_customer (lookup by customer_id, is_current=1) | SK lookup |
| product_sk | dim_product (lookup by product_id) | SK lookup |
| supplier_sk | dim_supplier (lookup by supplier_id) | SK lookup |
| order_id | order_header.order_id | Degenerate dim (no lookup) |
| quantity | order_line.quantity | Direct |
| gross_amount | order_line.quantity × order_line.unit_price | FULL_Sales |
| discount_amount | gross_amount × order_line.discount | FULL_Sales |
| net_amount | gross_amount − discount_amount | FULL_Sales |
| shipping_cost | order_header.shipping_cost | Direct |
