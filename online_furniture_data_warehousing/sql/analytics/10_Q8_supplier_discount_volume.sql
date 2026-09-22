-- =============================================================================
-- Q8 -- Supplier Discount behaviour vs. order volume
-- Which suppliers' products carry the highest average Discount rate,
-- and does that correlate with order volume?
-- Dimensions: DIM_Supplier
-- =============================================================================

SELECT
    ds.SupplierName,
    COUNT(*)                                                            AS order_line_count,
    SUM(fs.Quantity)                                                    AS total_units_sold,
    ROUND(SUM(fs.NetAmount), 2)                                        AS total_net_revenue,
    ROUND(
        100.0 * SUM(fs.DiscountAmount) / NULLIF(SUM(fs.GrossAmount), 0),
    2)                                                                  AS avg_discount_pct,
    ROUND(SUM(fs.NetAmount) / NULLIF(COUNT(*), 0), 2)                  AS avg_revenue_per_line
FROM FACT_Sales  fs
JOIN DIM_Supplier ds ON fs.SupplierSk = ds.SupplierSk
GROUP BY ds.SupplierName
ORDER BY avg_discount_pct DESC;
