-- =============================================================================
-- Analytical Queries  |  Online Furniture DWH
-- All queries run against the star schema (fact_sales + dim_* tables)
-- =============================================================================


-- =============================================================================
-- Q1 — Revenue and discount by category over time
-- How does net revenue develop per top-level product category and quarter,
-- and which category carries the highest discount share?
-- Dimensions: dim_date, dim_product
-- =============================================================================

SELECT
    dp.top_category_name,
    dd.year,
    dd.quarter,
    SUM(fs.net_amount)                                                  AS net_revenue,
    SUM(fs.gross_amount)                                                AS gross_revenue,
    SUM(fs.discount_amount)                                             AS total_discount,
    ROUND(
        100.0 * SUM(fs.discount_amount) / NULLIF(SUM(fs.gross_amount), 0),
    2)                                                                  AS discount_share_pct
FROM fact_sales  fs
JOIN dim_date    dd ON fs.date_sk    = dd.date_sk
JOIN dim_product dp ON fs.product_sk = dp.product_sk
GROUP BY dp.top_category_name, dd.year, dd.quarter
ORDER BY dd.year, dd.quarter, net_revenue DESC;


-- =============================================================================
-- Q2a — Average order value by PLZ region
-- Which postal code regions generate the highest average order value?
-- Dimensions: dim_customer, dim_date
-- Note: order value = sum of net line amounts + shipping cost (allocated once per order)
-- =============================================================================

WITH order_totals AS (
    SELECT
        dc.plz_region,
        fs.order_id,
        SUM(fs.net_amount) + MAX(fs.shipping_cost) AS order_value
    FROM fact_sales  fs
    JOIN dim_customer dc ON fs.customer_sk = dc.customer_sk
    WHERE dc.is_current = 1
    GROUP BY dc.plz_region, fs.order_id
)
SELECT
    plz_region,
    COUNT(DISTINCT order_id)        AS order_count,
    ROUND(AVG(order_value), 2)      AS avg_order_value,
    ROUND(SUM(order_value), 2)      AS total_revenue
FROM order_totals
GROUP BY plz_region
ORDER BY avg_order_value DESC;


-- =============================================================================
-- Q2b — Product category mix by PLZ region
-- Does the category mix differ between postal code regions?
-- Dimensions: dim_customer, dim_product
-- =============================================================================

SELECT
    dc.plz_region,
    dp.top_category_name,
    SUM(fs.net_amount)                                                  AS net_revenue,
    ROUND(
        100.0 * SUM(fs.net_amount)
            / SUM(SUM(fs.net_amount)) OVER (PARTITION BY dc.plz_region),
    1)                                                                  AS category_share_pct
FROM fact_sales  fs
JOIN dim_customer dc ON fs.customer_sk = dc.customer_sk
JOIN dim_product  dp ON fs.product_sk  = dp.product_sk
WHERE dc.is_current = 1
GROUP BY dc.plz_region, dp.top_category_name
ORDER BY dc.plz_region, net_revenue DESC;


-- =============================================================================
-- Q-S1 — Supplier revenue by quarter
-- Which suppliers generate the most net revenue per quarter, and how has
-- their share shifted over the two-year period?
-- Dimensions: dim_supplier, dim_date
-- =============================================================================

SELECT
    ds.supplier_name,
    dd.year,
    dd.quarter,
    SUM(fs.net_amount)                                                  AS net_revenue,
    COUNT(*)                                                            AS order_line_count,
    ROUND(
        100.0 * SUM(fs.net_amount)
            / SUM(SUM(fs.net_amount)) OVER (PARTITION BY dd.year, dd.quarter),
    2)                                                                  AS revenue_share_pct
FROM fact_sales  fs
JOIN dim_supplier ds ON fs.supplier_sk = ds.supplier_sk
JOIN dim_date     dd ON fs.date_sk     = dd.date_sk
GROUP BY ds.supplier_name, dd.year, dd.quarter
ORDER BY dd.year, dd.quarter, net_revenue DESC;


-- =============================================================================
-- Q-S2 — Supplier discount behaviour vs. order volume
-- Which suppliers' products carry the highest average discount rate,
-- and does that correlate with order volume?
-- Dimensions: dim_supplier
-- =============================================================================

SELECT
    ds.supplier_name,
    COUNT(*)                                                            AS order_line_count,
    SUM(fs.quantity)                                                    AS total_units_sold,
    ROUND(SUM(fs.net_amount), 2)                                        AS total_net_revenue,
    ROUND(
        100.0 * SUM(fs.discount_amount) / NULLIF(SUM(fs.gross_amount), 0),
    2)                                                                  AS avg_discount_pct,
    ROUND(SUM(fs.net_amount) / NULLIF(COUNT(*), 0), 2)                  AS avg_revenue_per_line
FROM fact_sales  fs
JOIN dim_supplier ds ON fs.supplier_sk = ds.supplier_sk
GROUP BY ds.supplier_name
ORDER BY avg_discount_pct DESC;


-- =============================================================================
-- Q3a — Peak order volume by weekday
-- Which weekdays see the highest order volume across the two-year period?
-- Dimensions: dim_date
-- =============================================================================

SELECT
    dd.weekday_name,
    dd.weekday,
    COUNT(DISTINCT fs.order_id)             AS order_count,
    SUM(fs.quantity)                        AS total_units,
    ROUND(SUM(fs.net_amount), 2)            AS net_revenue
FROM fact_sales  fs
JOIN dim_date    dd ON fs.date_sk = dd.date_sk
GROUP BY dd.weekday, dd.weekday_name
ORDER BY order_count DESC;


-- =============================================================================
-- Q3b — Top 10 peak calendar weeks
-- Which calendar weeks see the highest order volume?
-- Dimensions: dim_date
-- =============================================================================

SELECT
    dd.year,
    dd.calendar_week,
    COUNT(DISTINCT fs.order_id)             AS order_count,
    ROUND(SUM(fs.net_amount), 2)            AS net_revenue
FROM fact_sales  fs
JOIN dim_date    dd ON fs.date_sk = dd.date_sk
GROUP BY dd.year, dd.calendar_week
ORDER BY order_count DESC
LIMIT 10;


-- =============================================================================
-- Q4 — Discount rate vs. quantity sold and net revenue (discount effectiveness)
-- Does a higher discount rate correlate with higher quantity or net revenue per line?
-- Dimensions: fact_sales
-- =============================================================================

SELECT
    CASE
        WHEN discount_amount = 0.0                                THEN '0%   (no discount)'
        WHEN CAST(discount_amount AS REAL)/gross_amount < 0.05   THEN '1–5%'
        WHEN CAST(discount_amount AS REAL)/gross_amount < 0.10   THEN '5–10%'
        WHEN CAST(discount_amount AS REAL)/gross_amount < 0.15   THEN '10–15%'
        WHEN CAST(discount_amount AS REAL)/gross_amount < 0.20   THEN '15–20%'
        ELSE                                                           '20%+'
    END                                                                 AS discount_bucket,
    COUNT(*)                                                            AS order_line_count,
    ROUND(AVG(quantity), 2)                                             AS avg_quantity,
    ROUND(AVG(net_amount), 2)                                           AS avg_net_amount_per_line,
    ROUND(SUM(net_amount), 2)                                           AS total_net_revenue
FROM fact_sales
GROUP BY discount_bucket
ORDER BY MIN(CAST(discount_amount AS REAL) / gross_amount);


-- =============================================================================
-- Q5 — Revenue and discount share by product price segment
-- Budget (<€200) / Mid-range (€200–€799) / Premium (≥€800)
-- Dimensions: dim_product
-- =============================================================================

SELECT
    CASE
        WHEN dp.list_price < 200.0   THEN 'Budget (< €200)'
        WHEN dp.list_price < 800.0   THEN 'Mid-range (€200 – €799)'
        ELSE                              'Premium (≥ €800)'
    END                                                                 AS price_segment,
    COUNT(*)                                                            AS order_line_count,
    SUM(fs.quantity)                                                    AS total_units_sold,
    ROUND(SUM(fs.net_amount), 2)                                        AS net_revenue,
    ROUND(
        100.0 * SUM(fs.discount_amount) / NULLIF(SUM(fs.gross_amount), 0),
    2)                                                                  AS discount_share_pct
FROM fact_sales  fs
JOIN dim_product dp ON fs.product_sk = dp.product_sk
GROUP BY price_segment
ORDER BY MIN(dp.list_price);


-- =============================================================================
-- Q6 — Federal state revenue growth: Year 1 (2024) → Year 2 (2025)
-- Which federal states show the strongest revenue growth?
-- Dimensions: dim_customer, dim_date
-- =============================================================================

WITH yearly AS (
    SELECT
        dc.federal_state,
        dd.year,
        SUM(fs.net_amount)                  AS net_revenue
    FROM fact_sales  fs
    JOIN dim_customer dc ON fs.customer_sk = dc.customer_sk
    JOIN dim_date     dd ON fs.date_sk     = dd.date_sk
    WHERE dc.is_current = 1
    GROUP BY dc.federal_state, dd.year
)
SELECT
    y1.federal_state,
    ROUND(y1.net_revenue, 2)                AS revenue_2024,
    ROUND(y2.net_revenue, 2)                AS revenue_2025,
    ROUND(
        100.0 * (y2.net_revenue - y1.net_revenue) / NULLIF(y1.net_revenue, 0),
    2)                                      AS growth_pct
FROM yearly y1
JOIN yearly y2
    ON  y1.federal_state = y2.federal_state
    AND y1.year = 2024
    AND y2.year = 2025
ORDER BY growth_pct DESC;
