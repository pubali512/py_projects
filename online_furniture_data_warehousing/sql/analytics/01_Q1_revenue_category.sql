-- =============================================================================
-- Q1 -- Revenue and Discount by category over time
-- How does net revenue develop per top-level product category and Quarter,
-- and which category carries the highest Discount share?
-- Dimensions: DIM_Date, DIM_Product
-- =============================================================================

SELECT
    dp.TopCategoryName,
    dd.Year,
    dd.Quarter,
    SUM(fs.NetAmount)                                                  AS net_revenue,
    SUM(fs.GrossAmount)                                                AS gross_revenue,
    SUM(fs.DiscountAmount)                                             AS total_discount,
    ROUND(
        100.0 * SUM(fs.DiscountAmount) / NULLIF(SUM(fs.GrossAmount), 0),
    2)                                                                  AS discount_share_pct
FROM FACT_Sales  fs
JOIN DIM_Date    dd ON fs.DateSk    = dd.DateSk
JOIN DIM_Product dp ON fs.ProductSk = dp.ProductSk
GROUP BY dp.TopCategoryName, dd.Year, dd.Quarter
ORDER BY dd.Year, dd.Quarter, net_revenue DESC;
