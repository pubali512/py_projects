-- =============================================================================
-- Q3a -- Peak order volume by weekday
-- Which weekdays see the highest order volume across the two-year period?
-- Dimensions: DIM_Date
-- =============================================================================

SELECT
    dd.weekday_name,
    dd.weekday,
    COUNT(DISTINCT fs.order_id)             AS order_count,
    SUM(fs.quantity)                        AS total_units,
    ROUND(SUM(fs.net_amount), 2)            AS net_revenue
FROM FACT_Sales  fs
JOIN DIM_Date    dd ON fs.date_sk = dd.date_sk
GROUP BY dd.weekday, dd.weekday_name
ORDER BY order_count DESC;
