-- =============================================================================
-- FULL_Sales -- Transform: RAW_ -> FULL_BusinessDB_DWH_Sales
-- Joins order lines, order headers, and products.
-- Pre-computes GrossAmount, DiscountAmount, and NetAmount for each line.
--
--   GrossAmount    = Quantity * UnitPrice
--   DiscountAmount = GrossAmount * Discount
--   NetAmount      = GrossAmount - DiscountAmount
-- =============================================================================

DELETE FROM FULL_BusinessDB_DWH_Sales;

INSERT INTO FULL_BusinessDB_DWH_Sales
SELECT
    ol.OrderLineId,
    ol.OrderId,
    oh.OrderDate,
    oh.CustomerId,
    ol.ProductId,
    p.SupplierId,
    ol.Quantity,
    ol.UnitPrice,
    ol.Discount,
    oh.ShippingCost,
    ROUND(ol.Quantity * ol.UnitPrice, 2)                        AS GrossAmount,
    ROUND(ol.Quantity * ol.UnitPrice * ol.Discount, 2)          AS DiscountAmount,
    ROUND(ol.Quantity * ol.UnitPrice * (1.0 - ol.Discount), 2)  AS NetAmount
FROM RAW_BusinessDB_OrderLine   ol
JOIN RAW_BusinessDB_OrderHeader oh ON ol.OrderId   = oh.OrderId
JOIN RAW_BusinessDB_Product     p  ON ol.ProductId = p.ProductId;
