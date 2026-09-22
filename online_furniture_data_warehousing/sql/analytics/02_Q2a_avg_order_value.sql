-- =============================================================================
-- Q2a — Average order value by PLZ region (Part A)
-- Which postal code regions generate the highest average order value?
-- Note: order value = sum of net line amounts + shipping cost (once per order)
-- Dimensions: dim_customer
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
