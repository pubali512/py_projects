-- =============================================================================
-- Q4 -- Discount effectiveness
-- Does a higher Discount rate correlate with higher Quantity sold
-- or net revenue per order line?
-- Dimensions: FACT_Sales
-- =============================================================================

SELECT
    CASE
        WHEN DiscountAmount = 0.0                                THEN '0%   (no Discount)'
        WHEN CAST(DiscountAmount AS REAL)/GrossAmount < 0.05   THEN '1-5%'
        WHEN CAST(DiscountAmount AS REAL)/GrossAmount < 0.10   THEN '5-10%'
        WHEN CAST(DiscountAmount AS REAL)/GrossAmount < 0.15   THEN '10-15%'
        WHEN CAST(DiscountAmount AS REAL)/GrossAmount < 0.20   THEN '15-20%'
        ELSE                                                           '20%+'
    END                                                                 AS discount_bucket,
    COUNT(*)                                                            AS order_line_count,
    ROUND(AVG(Quantity), 2)                                             AS avg_quantity,
    ROUND(AVG(NetAmount), 2)                                           AS avg_net_amount_per_line,
    ROUND(SUM(NetAmount), 2)                                           AS total_net_revenue
FROM FACT_Sales
GROUP BY discount_bucket
ORDER BY MIN(CAST(DiscountAmount AS REAL) / GrossAmount);
