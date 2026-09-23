# Data generation 
    - data_gen/generate_data.py 
        -Business DB created using faker (`01_create_business_db.sql`)

# Entry point 

- run_all_etl 
    - run_etl_extract()
        - apply_dwh_ddl -> Creates RAW_, FULL_, DIM_, FACT_ tables (if they do not exist -> `02_create_dwh.sql`)
        - extract_to_raw 
            - Iterates over `_RAW_MAP` (Business DB to RAW_ table name mapping, e.g., Customer to `RAW_BusinessDB_Customer`)
            - For each `RAW_` table, deletes data and copies from the corresponding Business DB table.
    - run_etl_transform()
        - Executes the 3 transformation scripts for the 3 FULL_ tables (from `sql/transform/`)
        - Each script performs the following: Deletes existing table data and copies data from `RAW_` tables and transforms them. 
            - For customers -> Addiitonal PlzZone and PlzRegion are added 
            - For products -> Category name and top category names are added (by joining with the Category table)
            - For sales -> Full sales table is created by joining order header and order line as well a product. 
    - run_etl_dim_date()
    - run_etl_dim_supplier()
    - run_etl_dim_product()
    - run_etl_dim_customer()
    - run_etl_fact_sales()