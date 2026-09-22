-- =============================================================================
-- Q5 -- Revenue and discount share by product price segment
-- How does revenue and discount compare across Budget (<EUR 200) /
-- Mid-range (EUR 200-799) / Premium (>=EUR 800) product segments?
-- Dimensions: dim_product
-- =============================================================================

SELECT
    CASE
        WHEN dp.list_price < 200.0   THEN 'Budget (< EUR 200)'
        WHEN dp.list_price < 800.0   THEN 'Mid-range (EUR 200-799)'
        ELSE                              'Premium (>= EUR 800)'
    END                                                                 AS price_segment,
    COUNT(*)                                                            AS order_line_count,
    SUM(fs.quantity)                                                    AS total_units_sold,
    ROUND(SUM(fs.net_amount), 2)                                        AS net_revenue,
    ROUND(
        100.0 * SUM(fs.discount_amount) / NULLIF(SUM(fs.gross_amount), 0),
    2)                                                                  AS discount_share_pct
FROM fact_sales  fs
JOIN dim_product dp ON fs.product_sk = dp.product_sk
GROUP BY price_segment
ORDER BY MIN(dp.list_price);
