# DWH — Dimensional Model (Star Schema)

Diagram: [erm_dwh.drawio](diagrams/erm_dwh.drawio)

---

## Grain

`fact_sales` — one row per order line.

---

## Tables

### Fact Table

| Column | Type | Description |
|---|---|---|
| sales_sk | PK | Surrogate key |
| date_sk | FK | → dim_date |
| customer_sk | FK | → dim_customer (SCD2 current row) |
| product_sk | FK | → dim_product |
| supplier_sk | FK | → dim_supplier |
| order_id | — | Degenerate dimension |
| quantity | measure | Units ordered |
| gross_amount | measure | quantity × unit_price |
| discount_amount | measure | gross × discount rate |
| net_amount | measure | gross − discount |
| shipping_cost | measure | Per-order cost (from order_header) |

### Dimension Tables

| Table | Rows | SCD | Special columns |
|---|---|---|---|
| `dim_date` | 731 | 0 | day, month, quarter, year, weekday, calendar_week |
| `dim_customer` | 5,000+ | **2** | plz_region, plz_zone, valid_from, valid_to, is_current |
| `dim_product` | 120 | **1** | category_name, top_category_name (hierarchy flattened) |
| `dim_supplier` | 20 | 0 | city, country |

---

## Logical Model

```
dim_date ──────────────────────────────────────────────────────┐
                                                               │
dim_customer ──────────────────────── fact_sales ──────── dim_product
                                             │
dim_supplier ──────────────────────────────┘
```

Foreign keys in `fact_sales`: date_sk, customer_sk, product_sk, supplier_sk.

---

## SCD Strategy Summary

| Type | Attribute(s) | Justification |
|---|---|---|
| SCD 0 | Natural keys, order_date | Immutable |
| SCD 1 | product_name, list_price, colour, material | Corrections only; history not needed |
| SCD 2 | customer address (postal_code, city, federal_state, plz_region, plz_zone) | Relocation changes region; history matters for Q2 / Q6 |

SCD 2 columns on `dim_customer`: `valid_from`, `valid_to` (NULL = active), `is_current` (0/1).

ETL logic: new address → expire current row (valid_to = today, is_current = 0) → insert new row.
