-- =============================================================================
-- Q7 -- Supplier revenue by Quarter
-- Which suppliers generate the most net revenue per Quarter,
-- and how has their share shifted over the two-Year period?
-- Dimensions: DIM_Supplier, DIM_Date
-- =============================================================================

SELECT
    ds.SupplierName,
    dd.Year,
    dd.Quarter,
    ROUND(SUM(fs.NetAmount), 2)                                        AS net_revenue,
    COUNT(*)                                                            AS order_line_count,
    ROUND(
        100.0 * SUM(fs.NetAmount)
            / SUM(SUM(fs.NetAmount)) OVER (PARTITION BY dd.Year, dd.Quarter),
    2)                                                                  AS revenue_share_pct
FROM FACT_Sales  fs
JOIN DIM_Supplier ds ON fs.SupplierSk = ds.SupplierSk
JOIN DIM_Date     dd ON fs.DateSk     = dd.DateSk
GROUP BY ds.SupplierName, dd.Year, dd.Quarter
ORDER BY dd.Year, dd.Quarter, net_revenue DESC;
