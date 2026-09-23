import urllib
from sqlalchemy import create_engine, text
from ETL_Control_Table import run_etl_control_table
from ETL_Kunden import run_etl_kunden
from ETL_Artikel import run_etl_artikel
from ETL_Kassa import run_etl_kassa
from ETL_Zeit import run_etl_zeit
from ETL_F_Einkaeufe import run_etl_f_einkaeufe

params_target = (
    "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;"
    "DATABASE=DWH_NorthWind_B;Trusted_Connection=yes;Encrypt=no;"
)
con_str_target = urllib.parse.quote_plus(params_target)
engine_target = create_engine(f"mssql+pyodbc:///?odbc_connect={con_str_target}")

def clear_all_facts():
    with engine_target.connect() as conn:
        conn.execute(text("DELETE FROM dwh1.F_Einkaeufe"))
        conn.commit()

def run_all_etl():
    clear_all_facts()  # zuerst Fakten löschen

    run_etl_control_table()
    run_etl_kunden()
    run_etl_artikel()
    run_etl_kassa()
    run_etl_zeit(1996) # ...
    run_etl_zeit(2002)
    run_etl_f_einkaeufe()

if __name__ == "__main__":
    run_all_etl()
