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


def extract_kassa():
    query = "SELECT * FROM dbo.Kassa"  # Schema hinzugefügt
    df = pd.read_sql(query, engine_source)
    return df


def transform_kassa(df):
    # Kassa-Spalte rausnehmen, weil Identity in DB
    df_clean = df[['Filiale', 'Filialbezirk', 'Filialoberbezirk',
                   'FilialLandkreis', 'FilialBundesland', 'FilialStaat']]
    return df_clean



def insert_dummy_kassa():
    with engine_target.connect() as conn:
        conn.execute(text("SET IDENTITY_INSERT dwh1.Kassa ON;"))
        conn.execute(text("""
            IF NOT EXISTS (SELECT 1 FROM dwh1.Kassa WHERE Kassa = -1)
            BEGIN
                INSERT INTO dwh1.Kassa (Kassa, Filiale, Filialbezirk, Filialoberbezirk, FilialLandkreis, FilialBundesland, FilialStaat)
                VALUES (-1, 'Unbekannt', 'Unbekannt', 'Unbekannt', 'Unbekannt', 'Unbekannt', 'Unbekannt')
            END
        """))
        conn.execute(text("SET IDENTITY_INSERT dwh1.Kassa OFF;"))
        conn.commit()
    print("Dummy-Kassa mit Kassa=-1 eingefügt (sofern noch nicht vorhanden).")


def load_kassa(df):
    with engine_target.connect() as conn:
        # Löschen der Faktentabelle F_Einkaeufe abhängig von Anwendung, falls nötig entkommentieren
        #conn.execute(text("DELETE FROM dwh1.F_Einkaeufe"))

        conn.execute(text("DELETE FROM dwh1.Kassa"))
        conn.commit()
    df.to_sql('Kassa', engine_target, schema='dwh1', if_exists='append', index=False)
    print("Kassadaten geladen.")
    # Dummy-Kassa danach einfügen
    insert_dummy_kassa()


def run_etl_kassa():
    df_raw = extract_kassa()
    df_transformed = transform_kassa(df_raw)
    load_kassa(df_transformed)
    print("ETL Kassa abgeschlossen.")


if __name__ == "__main__":
    run_etl_kassa()
