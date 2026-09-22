-- =============================================================================
-- Q3b -- Peak order volume by calendar week (Top 10)
-- Which calendar weeks see the highest order volume?
-- Dimensions: DIM_Date
-- =============================================================================

SELECT
    dd.Year,
    dd.CalendarWeek,
    COUNT(DISTINCT fs.OrderId)             AS order_count,
    ROUND(SUM(fs.NetAmount), 2)            AS net_revenue
FROM FACT_Sales  fs
JOIN DIM_Date    dd ON fs.DateSk = dd.DateSk
GROUP BY dd.Year, dd.CalendarWeek
ORDER BY order_count DESC
LIMIT 10;
