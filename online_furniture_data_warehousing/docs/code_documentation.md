# Data generation 
    - data_gen/generate_data.py 
        -Business DB created using faker (`sql/01_create_business_db.sql`)

# Execution flow  

- run_all_etl (entire data pipeline) 
    - **Stage 1:** run_etl_extract() -> Copies business DB to RAW_ tables in the data warehouse
        - apply_dwh_ddl -> Creates RAW_, FULL_, DIM_, FACT_ tables (if they do not exist -> `sql/02_create_dwh.sql`)
        - extract_to_raw 
            - Iterates over `_RAW_MAP` (Business DB to RAW_ table name mapping, e.g., Customer to `RAW_BusinessDB_Customer`)
            - For each `RAW_` table, deletes data and copies from the corresponding Business DB table.
    - **Stage 2:** run_etl_transform() -> Transforms RAW_ tables into FULL_ tables
        - Executes the 3 transformation scripts for the 3 FULL_ tables (from `sql/transform/`)
        - Each script performs the following: Deletes existing table data and copies data from `RAW_` tables and transforms them. 
            - For customers -> Addiitonal PlzZone and PlzRegion are added 
            - For products -> Category name and top category names are added (by joining with the Category table) (Flattening of category hierarchy)
            - For sales -> Full sales table is created by joining order header and order line as well a product (i.e., each line corresponds to a order line)
    - **Stage 3:** Update dimension and fact tables
        - run_etl_dim_date()
            - DIM_Date stores all unique order dates with a surrogate key in the form <<YYYYMMDD> (i.e., by replacing the **-** in the original date with empty string)
        - run_etl_dim_supplier()
            - Inserts new supplier ID with a surrogate key into DIM_Supplier (If new suppliers are added to the business DB)
        - run_etl_dim_product()
            - Inserts a new product ID with a surrogate key into DIM_Product (If new products are added to the business DB)
            - If any attribute of a product is updated in the business DB, the corresponding record in DIM_Product is also updated (SCD 1 approach)
        - run_etl_dim_customer()
            - Inserts a new customer ID with a surrogate key into DIM_Customer (If new customers are added to the business DB)
            - If the address of a customer is changed then the corresponding record in DIM_Customer is also updated. (SCD 2 approach)
        - run_etl_fact_sales()
            - Inserts new sales records into FACT_Sales (If new sales are added to the business DB) 
            - For customers, the current surrogate key from DIM_Customer is used to maintain the relationship between sales and customers (IsCurrent = 1)


