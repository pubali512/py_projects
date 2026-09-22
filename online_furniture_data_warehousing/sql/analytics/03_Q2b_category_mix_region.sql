-- =============================================================================
-- Q2b -- Product category mix by PLZ region (Part B)
-- Does the product category mix differ between postal code regions?
-- Dimensions: DIM_Customer, DIM_Product
-- =============================================================================

SELECT
    dc.PlzRegion,
    dp.TopCategoryName,
    ROUND(SUM(fs.NetAmount), 2)                                        AS net_revenue,
    ROUND(
        100.0 * SUM(fs.NetAmount)
            / SUM(SUM(fs.NetAmount)) OVER (PARTITION BY dc.PlzRegion),
    1)                                                                  AS category_share_pct
FROM FACT_Sales  fs
JOIN DIM_Customer dc ON fs.CustomerSk = dc.CustomerSk
JOIN DIM_Product  dp ON fs.ProductSk  = dp.ProductSk
WHERE dc.IsCurrent = 1
GROUP BY dc.PlzRegion, dp.TopCategoryName
ORDER BY dc.PlzRegion, net_revenue DESC;
