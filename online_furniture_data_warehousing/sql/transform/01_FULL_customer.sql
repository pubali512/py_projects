-- =============================================================================
-- FULL_Customer -- Transform: RAW_BusinessDB_Customer -> FULL_BusinessDB_DWH_Customer
-- Derives plz_region (first digit of postal_code) and
-- plz_zone (first two digits of postal_code) for regional analysis.
-- =============================================================================

DELETE FROM FULL_BusinessDB_DWH_Customer;

INSERT INTO FULL_BusinessDB_DWH_Customer
SELECT
    customer_id,
    first_name,
    last_name,
    email,
    street_address,
    postal_code,
    substr(postal_code, 1, 1)  AS plz_region,
    substr(postal_code, 1, 2)  AS plz_zone,
    city,
    federal_state,
    customer_since
FROM RAW_BusinessDB_Customer;
