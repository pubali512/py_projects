-- =============================================================================
-- FULL_Customer -- Transform: RAW_BusinessDB_Customer -> FULL_BusinessDB_DWH_Customer
-- Derives PlzRegion (first digit of PostalCode) and
-- PlzZone (first two digits of PostalCode) for regional analysis.
-- =============================================================================

DELETE FROM FULL_BusinessDB_DWH_Customer;

INSERT INTO FULL_BusinessDB_DWH_Customer
SELECT
    CustomerId,
    FirstName,
    LastName,
    Email,
    StreetAddress,
    PostalCode,
    substr(PostalCode, 1, 1)  AS PlzRegion,
    substr(PostalCode, 1, 2)  AS PlzZone,
    City,
    FederalState,
    CustomerSince
FROM RAW_BusinessDB_Customer;
