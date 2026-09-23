import urllib
import pyodbc
from sqlalchemy import create_engine, text
import pandas as pd

# Verbindung zur Quelldatenbank NORTHWND
params_source = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=NORTHWND;"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
)
con_str_source = urllib.parse.quote_plus(params_source)
engine_source = create_engine(f"mssql+pyodbc:///?odbc_connect={con_str_source}")

# Verbindung zur Zieldatenbank DWH_NorthWind_B
params_target = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=DWH_NorthWind_B;"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
)
con_str_target = urllib.parse.quote_plus(params_target)
engine_target = create_engine(f"mssql+pyodbc:///?odbc_connect={con_str_target}")

def extract_artikel():
    query = """
        SELECT * 
        FROM NORTHWND.dbo.Products p 
        INNER JOIN NORTHWND.dbo.Categories c ON p.CategoryID = c.CategoryID 
        INNER JOIN NORTHWND.dbo.Suppliers s ON p.SupplierId = s.SupplierId
    """
    df = pd.read_sql(query, engine_source)
    return df

def transform_artikel(df):
    df['Artikelgruppe'] = df['CategoryName'].fillna('N/A').str.strip().str[:25]
    df['Artikelobergruppe'] = df['CompanyName'].fillna('N/A').str.strip().str[:40]
    df_clean = df[['Artikelgruppe', 'Artikelobergruppe']]
    print(df_clean.head(15))
    return df_clean

def load_artikel(df):
    with engine_target.connect() as conn:
        # Vorgänger-Faktentabelle evtl. leeren, falls nötig
        conn.execute(text("DELETE FROM dwh1.F_Einkaeufe"))
        conn.execute(text("DELETE FROM dwh1.Artikel"))
        conn.commit()
    df.to_sql('Artikel', engine_target, schema='dwh1', if_exists='append', index=False)
    print("Artikeldaten geladen.")

def run_etl_artikel():
    df_raw = extract_artikel()
    df_transformed = transform_artikel(df_raw)
    load_artikel(df_transformed)
    print("ETL Artikel abgeschlossen.")

if __name__ == "__main__":
    run_etl_artikel()
