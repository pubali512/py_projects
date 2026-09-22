-- =============================================================================
-- Q8 — Supplier discount behaviour vs. order volume
-- Which suppliers' products carry the highest average discount rate,
-- and does that correlate with order volume?
-- Dimensions: dim_supplier
-- =============================================================================

SELECT
    ds.supplier_name,
    COUNT(*)                                                            AS order_line_count,
    SUM(fs.quantity)                                                    AS total_units_sold,
    ROUND(SUM(fs.net_amount), 2)                                        AS total_net_revenue,
    ROUND(
        100.0 * SUM(fs.discount_amount) / NULLIF(SUM(fs.gross_amount), 0),
    2)                                                                  AS avg_discount_pct,
    ROUND(SUM(fs.net_amount) / NULLIF(COUNT(*), 0), 2)                  AS avg_revenue_per_line
FROM fact_sales  fs
JOIN dim_supplier ds ON fs.supplier_sk = ds.supplier_sk
GROUP BY ds.supplier_name
ORDER BY avg_discount_pct DESC;
