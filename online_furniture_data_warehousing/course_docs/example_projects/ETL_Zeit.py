import pandas as pd
from sqlalchemy import create_engine, text
import urllib

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

def create_time_dimension(year):
    start_date = pd.Timestamp(f'{year}-01-01')
    end_date = pd.Timestamp(f'{year}-12-31')
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    df = pd.DataFrame({
        'Tag': dates.strftime('%Y%m%d'),
        'Woche': dates.isocalendar().week,
        'Monat': dates.month,
        'Year': dates.year
    })

    with engine_target.connect() as conn:
        conn.execute(text(f"DELETE FROM dwh1.Zeit WHERE Year = {year}"))
        conn.commit()

    df.to_sql('Zeit', engine_target, schema='dwh1', if_exists='append', index=False)
    print(f"Zeittabelle für {year} erfolgreich erstellt und geladen.")

def run_etl_zeit(year):
    create_time_dimension(year)
    print(f"ETL Zeit für {year} abgeschlossen.")

if __name__ == "__main__":
    run_etl_zeit(2023)
