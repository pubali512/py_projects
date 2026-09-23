import pandas as pd
from sqlalchemy import create_engine, text
import urllib

# Verbindung zur Staging-Datenbank
params_staging = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=NORTHWND;"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
)
con_str_staging = urllib.parse.quote_plus(params_staging)
engine_staging = create_engine(f"mssql+pyodbc:///?odbc_connect={con_str_staging}")

def create_control_table():
    sql_create = """
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'control_table')
    CREATE TABLE dbo.control_table (
        Last_loading_Date datetime,
        FactTableName varchar(100)
    )
    """
    with engine_staging.connect() as conn:
        conn.execute(text(sql_create))
        conn.commit()
    print("Control Table erstellt (sofern nicht existent).")

def insert_control_entry(last_date, fact_table_name):
    df_control = pd.DataFrame({
        'Last_loading_Date': [last_date],
        'FactTableName': [fact_table_name]
    })
    df_control.to_sql('control_table', engine_staging, schema='dbo', if_exists='append', index=False)
    print("Eintrag in Control Table eingefügt.")

def read_control_table():
    df = pd.read_sql("SELECT * FROM dbo.control_table", engine_staging)
    print("Inhalt der Control Table:")
    print(df)
    return df

def run_etl_control_table():
    create_control_table()
    insert_control_entry('1900-01-01', 'F_Einkaeufe')
    read_control_table()
    print("ETL Control Table abgeschlossen.")

if __name__ == "__main__":
    run_etl_control_table()
