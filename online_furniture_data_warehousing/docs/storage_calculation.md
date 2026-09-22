# Storage Space Calculation — Business DB

SQLite file: `data/furniture.db`

---

## Row counts (synthetic data)

| Table | Rows |
|---|---|
| supplier | 20 |
| category | 15 |
| product | 120 |
| customer | 5,000 |
| order_header | 30,000 |
| order_line | ~85,500 |
| **Total Business DB** | **~120,655** |

---

## Per-row size estimates

| Table | Estimated row size | Basis |
|---|---|---|
| supplier | 80 bytes | 4 columns: int + 3× varchar ~20 |
| category | 60 bytes | 3 columns: 2× int + varchar |
| product | 120 bytes | 7 columns: int, 2× varchar, real, 2× FK |
| customer | 250 bytes | 9 columns: int + 8× varchar/date |
| order_header | 100 bytes | 5 columns: 2× int + varchar + real + date |
| order_line | 60 bytes | 6 columns: 4× int/real + 2× FK |

---

## Storage estimates

| Table | Rows | Row size | Estimated |
|---|---|---|---|
| supplier | 20 | 80 B | 1.6 KB |
| category | 15 | 60 B | 0.9 KB |
| product | 120 | 120 B | 14.4 KB |
| customer | 5,000 | 250 B | 1.2 MB |
| order_header | 30,000 | 100 B | 2.9 MB |
| order_line | 85,500 | 60 B | 4.9 MB |
| **Subtotal (data)** | | | **~9.0 MB** |
| SQLite overhead (page headers, indexes, B-tree) | | | ~20-30% |
| **Total estimate** | | | **~11–12 MB** |

---

## Actual SQLite file size

```
data/furniture.db
```

SQLite stores all tables (Business DB + DWH + staging) in one file. Actual size depends on page size (default 4 KB) and fill factor.

DWH tables (star schema + staging) add approximately:

| Table | Rows | Additional storage |
|---|---|---|
| dim_date | 731 | ~0.1 MB |
| dim_customer | 5,000 | ~1.5 MB |
| dim_product | 120 | ~0.1 MB |
| dim_supplier | 20 | ~0.01 MB |
| fact_sales | 85,500 | ~7 MB |
| RAW_/FULL_ staging | ~170,000 total | ~12 MB |

**Total combined DB estimate: ~30–35 MB** (SQLite single-file, production databases would use separate source/DWH connections).
