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

# Extrahieren der Quelldaten
def extract_customers():
    query = "SELECT * FROM dbo.Customers"
    return pd.read_sql(query, engine_source)

# Bereinigung der Daten
def transform_customers(df):
    df['Region'] = df['Region'].fillna('')  # Nullwerte auffüllen
    df['PostalCode'] = df['PostalCode'].fillna('')
    df['Region'] = df['Region'].astype(str) + "_" + df['PostalCode'].astype(str)
    df = df.rename(columns={'Region': 'LandkreisdesKunden', 'City': 'WOhnOrtdesKunden'})
    df['LandkreisdesKunden'] = df['LandkreisdesKunden'].str.strip('_')
    return df[['WOhnOrtdesKunden', 'LandkreisdesKunden']]

# Laden der neuen Tabelle
def load_customers(df):
    with engine_target.connect() as conn:
        # Zuerst Faktentabelle leeren, um FK-Konflikt zu verhindern
        conn.execute(text("DELETE FROM dwh1.F_Einkaeufe"))
        # Danach Kundentabelle löschen
        conn.execute(text("DELETE FROM dwh1.Kunden"))
        conn.commit()
    df.to_sql('Kunden', engine_target, schema='dwh1', if_exists='append', index=False)
    print("Kundendaten geladen.")

# Automatisierung aller Funktionen
def run_etl_kunden():
    df_raw = extract_customers()
    df_transformed = transform_customers(df_raw)
    load_customers(df_transformed)
    print("ETL Kunden abgeschlossen.")

if __name__ == "__main__":
    run_etl_kunden()
