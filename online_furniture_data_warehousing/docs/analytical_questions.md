# Analytical Questions

All SQL in `sql/analytics/`. Run via `python python/run.py` (option 2).

---

## Mandatory Questions

### Q1 — Revenue and discount by category over time

`sql/analytics/01_Q1_revenue_category.sql`

Net revenue per top-level product category per quarter. Which category carries highest discount share?

Dimensions: `dim_date`, `dim_product`

Key result pattern: each of 5 categories × 8 quarters = 40 rows.

---

### Q2a — Average order value by PLZ region

`sql/analytics/02_Q2a_avg_order_value.sql`

Average order value (net lines + shipping) per postal code region (first digit, 0–9).

Dimension: `dim_customer`

---

### Q2b — Category mix by PLZ region

`sql/analytics/03_Q2b_category_mix_region.sql`

Category revenue share per PLZ region. Shows if buying patterns differ geographically.

Dimensions: `dim_customer`, `dim_product`

---

## Optional Questions

### Q3a — Peak weekday

`sql/analytics/04_Q3a_peak_weekday.sql`

Which weekdays see most orders? Dimension: `dim_date`

### Q3b — Peak calendar weeks (Top 10)

`sql/analytics/05_Q3b_peak_calendar_week.sql`

Which calendar weeks spike? Dimension: `dim_date`

---

### Q4 — Discount effectiveness

`sql/analytics/06_Q4_discount_effectiveness.sql`

Bucket order lines by discount rate. Compare avg quantity and avg net revenue across buckets.
Higher discount → lower avg net per line (expected). Dimension: `fact_sales`

---

### Q5 — Revenue by price segment

`sql/analytics/07_Q5_price_segment.sql`

Budget (<€200) / Mid-range (€200–€799) / Premium (≥€800).
Premium dominates volume in synthetic data. Dimension: `dim_product`

---

### Q6 — Federal state growth

`sql/analytics/08_Q6_state_growth.sql`

YoY revenue growth per Bundesland. Dimensions: `dim_customer`, `dim_date`

---

### Q7 — Supplier revenue by quarter

`sql/analytics/09_Q7_supplier_revenue_quarter.sql`

Top suppliers per quarter and revenue share shift over time.
Dimensions: `dim_supplier`, `dim_date`

---

### Q8 — Supplier discount vs. volume

`sql/analytics/10_Q8_supplier_discount_volume.sql`

Which suppliers offer highest average discount? Does high discount correlate with order volume?
Dimension: `dim_supplier`
