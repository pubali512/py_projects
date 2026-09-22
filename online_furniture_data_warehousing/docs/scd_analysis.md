# SCD Analysis

---

## Type Overview

| SCD Type | Behaviour | Columns |
|---|---|---|
| **0** | Never change. Original value kept forever. | Natural keys, order_date |
| **1** | Overwrite. No history. | Product catalogue attributes |
| **2** | New row. Old row expired. Full history. | Customer address |

---

## SCD 0 — Immutable Columns

| Column | Reason |
|---|---|
| customer_id, order_id, product_id, supplier_id, category_id | Natural keys — identity |
| order_date | Transaction timestamp — cannot retroactively change |

No ETL action. Values loaded once; never touched again.

---

## SCD 1 — Overwrite (dim_product)

| Column | Typical change | ETL action |
|---|---|---|
| product_name | Typo correction | UPDATE in place |
| list_price | Price change | UPDATE in place |
| colour, material | Catalogue correction | UPDATE in place |

History lost. Analytical questions Q1 and Q5 only need current product attributes — SCD 1 is sufficient.

SQL in `etl_dim_product.py` `load_dim_product()`:
```sql
UPDATE dim_product SET product_name=?, colour=?, material=?,
    list_price=?, category_name=?, top_category_name=?
WHERE product_id=?
```

MSSQL equivalent ALTER (if schema change needed):
```sql
-- No schema change required: columns already exist.
-- SCD1 is a data update, not a schema change.
```

---

## SCD 2 — Full History (dim_customer)

### Tracked columns

| Column | Why history matters |
|---|---|
| postal_code | Relocation changes PLZ region → affects Q2, Q6 |
| street_address | Confirms relocation vs. typo |
| city, federal_state, plz_region, plz_zone | Derived from postal_code — tracked together |

### Tracking columns

| Column | Type | Description |
|---|---|---|
| valid_from | DATE | Date row became active (customer_since for initial load; ETL date on change) |
| valid_to | DATE | Date row expired (NULL = still active) |
| is_current | INTEGER (0/1) | 1 = active row; 0 = historical |

### ETL logic (`etl_dim_customer.py`)

```
IF customer not in dim_customer:
    INSERT (valid_from=customer_since, valid_to=NULL, is_current=1)

ELSE IF postal_code OR street_address changed:
    UPDATE current row: valid_to=today, is_current=0
    INSERT new row:     valid_from=today, valid_to=NULL, is_current=1

ELSE:
    No action
```

### MSSQL ALTER equivalent

```sql
-- These columns are already in 02_create_dwh.sql.
-- For reference — if adding SCD2 to an existing table:
ALTER TABLE dim_customer ADD valid_from  DATE         NOT NULL DEFAULT GETDATE();
ALTER TABLE dim_customer ADD valid_to    DATE         NULL;
ALTER TABLE dim_customer ADD is_current  BIT          NOT NULL DEFAULT 1;
```

---

## Conclusion

| Dimension | SCD Type | Justification |
|---|---|---|
| dim_date | 0 | Dates are facts; immutable |
| dim_supplier | 0 | Supplier identity stable for this project |
| dim_product | 1 | Price/name corrections tolerated; no historical query needs it |
| dim_customer | 2 | Relocation changes region assignment → Q2 accuracy requires history |
