-- =============================================================================
-- Q4 -- Discount effectiveness
-- Does a higher discount rate correlate with higher quantity sold
-- or net revenue per order line?
-- Dimensions: FACT_Sales
-- =============================================================================

SELECT
    CASE
        WHEN discount_amount = 0.0                                THEN '0%   (no discount)'
        WHEN CAST(discount_amount AS REAL)/gross_amount < 0.05   THEN '1-5%'
        WHEN CAST(discount_amount AS REAL)/gross_amount < 0.10   THEN '5-10%'
        WHEN CAST(discount_amount AS REAL)/gross_amount < 0.15   THEN '10-15%'
        WHEN CAST(discount_amount AS REAL)/gross_amount < 0.20   THEN '15-20%'
        ELSE                                                           '20%+'
    END                                                                 AS discount_bucket,
    COUNT(*)                                                            AS order_line_count,
    ROUND(AVG(quantity), 2)                                             AS avg_quantity,
    ROUND(AVG(net_amount), 2)                                           AS avg_net_amount_per_line,
    ROUND(SUM(net_amount), 2)                                           AS total_net_revenue
FROM FACT_Sales
GROUP BY discount_bucket
ORDER BY MIN(CAST(discount_amount AS REAL) / gross_amount);
