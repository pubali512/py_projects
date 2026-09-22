-- =============================================================================
-- Q6 — Federal state revenue growth: Year 1 (2024) vs Year 2 (2025)
-- Which federal states show the strongest revenue growth?
-- Dimensions: dim_customer, dim_date
-- =============================================================================

WITH yearly AS (
    SELECT
        dc.federal_state,
        dd.year,
        SUM(fs.net_amount)                  AS net_revenue
    FROM fact_sales  fs
    JOIN dim_customer dc ON fs.customer_sk = dc.customer_sk
    JOIN dim_date     dd ON fs.date_sk     = dd.date_sk
    WHERE dc.is_current = 1
    GROUP BY dc.federal_state, dd.year
)
SELECT
    y1.federal_state,
    ROUND(y1.net_revenue, 2)                AS revenue_2024,
    ROUND(y2.net_revenue, 2)                AS revenue_2025,
    ROUND(
        100.0 * (y2.net_revenue - y1.net_revenue) / NULLIF(y1.net_revenue, 0),
    2)                                      AS growth_pct
FROM yearly y1
JOIN yearly y2
    ON  y1.federal_state = y2.federal_state
    AND y1.year = 2024
    AND y2.year = 2025
ORDER BY growth_pct DESC;
