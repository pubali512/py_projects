-- =============================================================================
-- Q6 -- Federal state revenue growth: Year 1 (2024) vs Year 2 (2025)
-- Which federal states show the strongest revenue growth?
-- Dimensions: DIM_Customer, DIM_Date
-- =============================================================================

WITH yearly AS (
    SELECT
        dc.FederalState,
        dd.Year,
        SUM(fs.NetAmount)                  AS net_revenue
    FROM FACT_Sales  fs
    JOIN DIM_Customer dc ON fs.CustomerSk = dc.CustomerSk
    JOIN DIM_Date     dd ON fs.DateSk     = dd.DateSk
    WHERE dc.IsCurrent = 1
    GROUP BY dc.FederalState, dd.Year
)
SELECT
    y1.FederalState,
    ROUND(y1.net_revenue, 2)                AS revenue_2024,
    ROUND(y2.net_revenue, 2)                AS revenue_2025,
    ROUND(
        100.0 * (y2.net_revenue - y1.net_revenue) / NULLIF(y1.net_revenue, 0),
    2)                                      AS growth_pct
FROM yearly y1
JOIN yearly y2
    ON  y1.FederalState = y2.FederalState
    AND y1.Year = 2024
    AND y2.Year = 2025
ORDER BY growth_pct DESC;
