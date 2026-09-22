-- =============================================================================
-- Q7 — Supplier revenue by quarter
-- Which suppliers generate the most net revenue per quarter,
-- and how has their share shifted over the two-year period?
-- Dimensions: dim_supplier, dim_date
-- =============================================================================

SELECT
    ds.supplier_name,
    dd.year,
    dd.quarter,
    ROUND(SUM(fs.net_amount), 2)                                        AS net_revenue,
    COUNT(*)                                                            AS order_line_count,
    ROUND(
        100.0 * SUM(fs.net_amount)
            / SUM(SUM(fs.net_amount)) OVER (PARTITION BY dd.year, dd.quarter),
    2)                                                                  AS revenue_share_pct
FROM fact_sales  fs
JOIN dim_supplier ds ON fs.supplier_sk = ds.supplier_sk
JOIN dim_date     dd ON fs.date_sk     = dd.date_sk
GROUP BY ds.supplier_name, dd.year, dd.quarter
ORDER BY dd.year, dd.quarter, net_revenue DESC;
