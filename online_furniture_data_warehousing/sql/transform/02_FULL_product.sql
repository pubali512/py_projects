-- =============================================================================
-- FULL_Product -- Transform: RAW_BusinessDB_Product -> FULL_BusinessDB_DWH_Product
-- Flattens the two-level category hierarchy:
--   sub-category (CategoryName) + top-level category (TopCategoryName).
-- If a category has no parent, it is treated as the top-level itself.
-- =============================================================================

DELETE FROM FULL_BusinessDB_DWH_Product;

INSERT INTO FULL_BusinessDB_DWH_Product
SELECT
    p.ProductId,
    p.ProductName,
    p.Colour,
    p.Material,
    p.ListPrice,
    c.CategoryName,
    COALESCE(top.CategoryName, c.CategoryName) AS TopCategoryName,
    p.SupplierId
FROM RAW_BusinessDB_Product      p
JOIN RAW_BusinessDB_Category     c   ON p.CategoryId       = c.CategoryId
LEFT JOIN RAW_BusinessDB_Category top ON c.ParentCategoryId = top.CategoryId;
