-- =============================================================================
-- Q3 -- Top 2 product categories per federal state by net revenue
-- What are the two highest net revenue generating product categories per federal state?
-- =============================================================================

WITH state_cat_revenue AS (
    SELECT
        dc.FederalState,
        dp.TopCategoryName,
        ROUND(SUM(fs.NetAmount), 2)  AS net_revenue
    FROM FACT_Sales  fs
    JOIN DIM_Customer dc ON fs.CustomerSk = dc.CustomerSk
    JOIN DIM_Product  dp ON fs.ProductSk  = dp.ProductSk
    WHERE dc.IsCurrent = 1
    GROUP BY dc.FederalState, dp.TopCategoryName
),
ranked AS (
    SELECT
        FederalState,
        TopCategoryName,
        net_revenue,
        RANK() OVER (PARTITION BY FederalState ORDER BY net_revenue DESC) AS rnk
    FROM state_cat_revenue
)
SELECT FederalState, TopCategoryName, net_revenue
FROM ranked
WHERE rnk <= 2
ORDER BY FederalState, rnk;
