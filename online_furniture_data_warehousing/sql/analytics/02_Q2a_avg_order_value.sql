-- =============================================================================
-- Q2a -- Average order value by PLZ region (Part A)
-- Which postal code regions generate the highest average order value?
-- Note: order value = sum of net line amounts + shipping cost (once per order)
-- Dimensions: DIM_Customer
-- =============================================================================

WITH order_totals AS (
    SELECT
        dc.PlzRegion,
        fs.OrderId,
        SUM(fs.NetAmount) + MAX(fs.ShippingCost) AS order_value
    FROM FACT_Sales  fs
    JOIN DIM_Customer dc ON fs.CustomerSk = dc.CustomerSk
    WHERE dc.IsCurrent = 1
    GROUP BY dc.PlzRegion, fs.OrderId
)
SELECT
    PlzRegion,
    COUNT(DISTINCT OrderId)        AS order_count,
    ROUND(AVG(order_value), 2)      AS avg_order_value,
    ROUND(SUM(order_value), 2)      AS total_revenue
FROM order_totals
GROUP BY PlzRegion
ORDER BY avg_order_value DESC;
