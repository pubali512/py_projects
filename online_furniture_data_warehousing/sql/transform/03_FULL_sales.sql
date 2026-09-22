-- =============================================================================
-- FULL_Sales -- Transform: RAW_ -> FULL_BusinessDB_DWH_Sales
-- Joins order lines, order headers, and products.
-- Pre-computes gross_amount, discount_amount, and net_amount for each line.
--
--   gross_amount    = quantity * unit_price
--   discount_amount = gross_amount * discount
--   net_amount      = gross_amount - discount_amount
-- =============================================================================

DELETE FROM FULL_BusinessDB_DWH_Sales;

INSERT INTO FULL_BusinessDB_DWH_Sales
SELECT
    ol.order_line_id,
    ol.order_id,
    oh.order_date,
    oh.customer_id,
    ol.product_id,
    p.supplier_id,
    ol.quantity,
    ol.unit_price,
    ol.discount,
    oh.shipping_cost,
    ROUND(ol.quantity * ol.unit_price, 2)                        AS gross_amount,
    ROUND(ol.quantity * ol.unit_price * ol.discount, 2)          AS discount_amount,
    ROUND(ol.quantity * ol.unit_price * (1.0 - ol.discount), 2)  AS net_amount
FROM RAW_BusinessDB_OrderLine   ol
JOIN RAW_BusinessDB_OrderHeader oh ON ol.order_id   = oh.order_id
JOIN RAW_BusinessDB_Product     p  ON ol.product_id = p.product_id;
