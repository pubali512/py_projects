-- =============================================================================
-- Q2b -- Product category mix by PLZ region (Part B)
-- Does the product category mix differ between postal code regions?
-- Dimensions: DIM_Customer, DIM_Product
-- =============================================================================

SELECT
    dc.plz_region,
    dp.top_category_name,
    ROUND(SUM(fs.net_amount), 2)                                        AS net_revenue,
    ROUND(
        100.0 * SUM(fs.net_amount)
            / SUM(SUM(fs.net_amount)) OVER (PARTITION BY dc.plz_region),
    1)                                                                  AS category_share_pct
FROM FACT_Sales  fs
JOIN DIM_Customer dc ON fs.customer_sk = dc.customer_sk
JOIN DIM_Product  dp ON fs.product_sk  = dp.product_sk
WHERE dc.is_current = 1
GROUP BY dc.plz_region, dp.top_category_name
ORDER BY dc.plz_region, net_revenue DESC;
