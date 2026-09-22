-- =============================================================================
-- Q5 -- Revenue and Discount share by product price segment
-- How does revenue and Discount compare across Budget (<EUR 200) /
-- Mid-range (EUR 200-799) / Premium (>=EUR 800) product segments?
-- Dimensions: DIM_Product
-- =============================================================================

SELECT
    CASE
        WHEN dp.ListPrice < 200.0   THEN 'Budget (< EUR 200)'
        WHEN dp.ListPrice < 800.0   THEN 'Mid-range (EUR 200-799)'
        ELSE                              'Premium (>= EUR 800)'
    END                                                                 AS price_segment,
    COUNT(*)                                                            AS order_line_count,
    SUM(fs.Quantity)                                                    AS total_units_sold,
    ROUND(SUM(fs.NetAmount), 2)                                        AS net_revenue,
    ROUND(
        100.0 * SUM(fs.DiscountAmount) / NULLIF(SUM(fs.GrossAmount), 0),
    2)                                                                  AS discount_share_pct
FROM FACT_Sales  fs
JOIN DIM_Product dp ON fs.ProductSk = dp.ProductSk
GROUP BY price_segment
ORDER BY MIN(dp.ListPrice);
