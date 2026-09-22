-- =============================================================================
-- FULL_Product -- Transform: RAW_BusinessDB_Product -> FULL_BusinessDB_DWH_Product
-- Flattens the two-level category hierarchy:
--   sub-category (category_name) + top-level category (top_category_name).
-- If a category has no parent, it is treated as the top-level itself.
-- =============================================================================

DELETE FROM FULL_BusinessDB_DWH_Product;

INSERT INTO FULL_BusinessDB_DWH_Product
SELECT
    p.product_id,
    p.product_name,
    p.colour,
    p.material,
    p.list_price,
    c.category_name,
    COALESCE(top.category_name, c.category_name) AS top_category_name,
    p.supplier_id
FROM RAW_BusinessDB_Product      p
JOIN RAW_BusinessDB_Category     c   ON p.category_id       = c.category_id
LEFT JOIN RAW_BusinessDB_Category top ON c.parent_category_id = top.category_id;
