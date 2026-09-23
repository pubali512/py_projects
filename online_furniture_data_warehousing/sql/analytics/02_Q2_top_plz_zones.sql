-- =============================================================================
-- Q2 -- Top 10 PLZ zones by net revenue
-- Which 10 postal code zones (first 2 digits of the PLZ) generate the maximum net revenue?
-- =============================================================================

SELECT
    dc.PlzZone,
    COUNT(DISTINCT fs.OrderId)      AS order_count,
    ROUND(SUM(fs.NetAmount), 2)     AS total_net_revenue
FROM FACT_Sales  fs
JOIN DIM_Customer dc ON fs.CustomerSk = dc.CustomerSk
WHERE dc.IsCurrent = 1
GROUP BY dc.PlzZone
ORDER BY total_net_revenue DESC
LIMIT 10;
