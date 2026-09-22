-- =============================================================================
-- Q3a -- Peak order volume by Weekday
-- Which weekdays see the highest order volume across the two-Year period?
-- Dimensions: DIM_Date
-- =============================================================================

SELECT
    dd.WeekdayName,
    dd.Weekday,
    COUNT(DISTINCT fs.OrderId)             AS order_count,
    SUM(fs.Quantity)                        AS total_units,
    ROUND(SUM(fs.NetAmount), 2)            AS net_revenue
FROM FACT_Sales  fs
JOIN DIM_Date    dd ON fs.DateSk = dd.DateSk
GROUP BY dd.Weekday, dd.WeekdayName
ORDER BY order_count DESC;
