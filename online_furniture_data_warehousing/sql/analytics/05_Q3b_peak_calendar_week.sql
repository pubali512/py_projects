-- =============================================================================
-- Q3b — Peak order volume by calendar week (Top 10)
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
