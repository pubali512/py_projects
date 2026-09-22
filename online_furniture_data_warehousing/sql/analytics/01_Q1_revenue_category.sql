-- =============================================================================
-- Q1 -- Revenue and discount by category over time
-- How does net revenue develop per top-level product category and quarter,
-- and which category carries the highest discount share?
-- Dimensions: DIM_Date, DIM_Product
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
FROM FACT_Sales  fs
JOIN DIM_Date    dd ON fs.date_sk    = dd.date_sk
JOIN DIM_Product dp ON fs.product_sk = dp.product_sk
GROUP BY dp.top_category_name, dd.year, dd.quarter
ORDER BY dd.year, dd.quarter, net_revenue DESC;
