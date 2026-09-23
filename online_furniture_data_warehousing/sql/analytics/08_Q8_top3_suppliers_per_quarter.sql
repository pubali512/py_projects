-- =============================================================================
-- Q8 -- Top 3 suppliers by net revenue per quarter
-- Which 3 suppliers generate the most net revenue per quarter?
-- =============================================================================

WITH quarterly_revenue AS (
    SELECT
        dd.Year,
        dd.Quarter,
        ds.SupplierName,
        ROUND(SUM(fs.NetAmount), 2)  AS net_revenue,
        RANK() OVER (
            PARTITION BY dd.Year, dd.Quarter
            ORDER BY SUM(fs.NetAmount) DESC
        ) AS rnk
    FROM FACT_Sales  fs
    JOIN DIM_Date     dd ON fs.DateSk     = dd.DateSk
    JOIN DIM_Supplier ds ON fs.SupplierSk = ds.SupplierSk
    GROUP BY dd.Year, dd.Quarter, ds.SupplierName
)
SELECT Year, Quarter, SupplierName, net_revenue, rnk AS rank_in_quarter
FROM quarterly_revenue
WHERE rnk <= 3
ORDER BY Year, Quarter, rnk;
