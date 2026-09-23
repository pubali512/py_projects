import pandas as pd
from sqlalchemy import create_engine, text
import urllib
from datetime import datetime

# Verbindungen
params_target = (
    "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;"
    "DATABASE=DWH_NorthWind_B;Trusted_Connection=yes;Encrypt=no;"
)
con_str_target = urllib.parse.quote_plus(params_target)
engine_target = create_engine(f"mssql+pyodbc:///?odbc_connect={con_str_target}")

params_staging = (
    "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;"
    "DATABASE=NORTHWND;Trusted_Connection=yes;Encrypt=no;"
)
con_str_staging = urllib.parse.quote_plus(params_staging)
engine_staging = create_engine(f"mssql+pyodbc:///?odbc_connect={con_str_staging}")

def get_last_loading_date():
    query = "SELECT Last_loading_Date FROM dbo.control_table WHERE FactTableName = 'F_Einkaeufe'"
    df = pd.read_sql(query, engine_staging)
    if df.empty:
        return pd.Timestamp('1900-01-01')
    return pd.to_datetime(df['Last_loading_Date'].iloc[0])

def get_current_loading_date():
    return pd.Timestamp(datetime.now())

def delete_existing_facts(startdate, enddate):
    with engine_target.connect() as conn:
        conn.execute(text(f"""
            DELETE FROM dwh1.F_Einkaeufe 
            WHERE Tag >= '{startdate.strftime('%Y%m%d')}' AND Tag <= '{enddate.strftime('%Y%m%d')}'
        """))
        conn.commit()

def extract_raw_data(startdate, enddate):
    orders_query = f"""
        SELECT o.OrderID, o.OrderDate, o.CustomerID, c.City, c.Region, c.PostalCode
        FROM dbo.Orders o
        JOIN dbo.Customers c ON o.CustomerID = c.CustomerID
        WHERE o.OrderDate >= '{startdate.strftime('%Y-%m-%d')}' AND o.OrderDate <= '{enddate.strftime('%Y-%m-%d')}'
    """
    orders = pd.read_sql(orders_query, engine_staging)

    order_details = pd.read_sql("SELECT OrderID, ProductID, UnitPrice, Quantity FROM dbo.[Order Details]", engine_staging)

    products = pd.read_sql("SELECT ProductID, CategoryID, SupplierID FROM dbo.Products", engine_staging)

    categories = pd.read_sql("SELECT CategoryID, CategoryName FROM dbo.Categories", engine_staging)

    suppliers = pd.read_sql("SELECT SupplierID, CompanyName FROM dbo.Suppliers", engine_staging)

    customers_dim = pd.read_sql("SELECT Kunde, WOhnOrtdesKunden, LandkreisdesKunden FROM dwh1.Kunden", engine_target)

    artikel_dim = pd.read_sql("SELECT Artikelgruppe, Artikelobergruppe, Artikel FROM dwh1.Artikel", engine_target)

    return orders, order_details, products, categories, suppliers, customers_dim, artikel_dim

def transform_data(orders, order_details, products, categories, suppliers,
                   customers_dim, artikel_dim):
    df = orders.merge(order_details, on='OrderID', how='inner')

    df = df.merge(products, on='ProductID', how='left')

    df = df.merge(categories, on='CategoryID', how='left')

    df = df.merge(suppliers, on='SupplierID', how='left')

    df['LandkreisdesKunden'] = df['Region'].fillna('') + '_' + df['PostalCode'].fillna('')
    df['LandkreisdesKunden'] = df['LandkreisdesKunden'].str.strip('_')

    df = df.merge(customers_dim,
                  left_on=['City', 'LandkreisdesKunden'],
                  right_on=['WOhnOrtdesKunden', 'LandkreisdesKunden'], how='left')

    df['Artikelgruppe'] = df['CategoryName'].fillna('N/A').str.strip().str[:25]
    df['Artikelobergruppe'] = df['CompanyName'].fillna('N/A').str.strip().str[:40]

    df = df.merge(artikel_dim,
                  left_on=['Artikelgruppe', 'Artikelobergruppe'],
                  right_on=['Artikelgruppe', 'Artikelobergruppe'], how='left')

    # Kassa wird fest auf -1 gesetzt
    df['Kassa'] = -1

    df['OrderDate'] = pd.to_datetime(df['OrderDate'], errors='coerce')
    df['Tag'] = df['OrderDate'].dt.strftime('%Y%m%d')

    df_facts = df.groupby(['Kunde', 'Artikel', 'Kassa', 'Tag'], as_index=False).agg({
        'Quantity': 'sum',
        'UnitPrice': 'min',
    })

    df_facts.rename(columns={'Quantity': 'Menge', 'UnitPrice': 'Verkaufspreis'}, inplace=True)

    return df_facts

def load_facts(df):
    df.to_sql('F_Einkaeufe', engine_target, schema='dwh1', if_exists='append', index=False)
    print("Faktendaten geladen.")

def update_loading_date(date):
    with engine_staging.connect() as conn:
        conn.execute(text(f"""
            UPDATE dbo.control_table
            SET Last_loading_Date = '{date.strftime('%Y-%m-%d %H:%M:%S')}'
            WHERE FactTableName = 'F_Einkaeufe'
        """))
        conn.commit()

def run_etl_f_einkaeufe():
    #startdate = get_last_loading_date()
    #loading_date = get_current_loading_date()
    startdate = pd.Timestamp('1900-01-01')
    loading_date = pd.Timestamp.now()
    print(f"Lade F_Einkaeufe von {startdate.date()} bis {loading_date.date()}...")

    delete_existing_facts(startdate, loading_date)

    orders, order_details, products, categories, suppliers, customers_dim, artikel_dim = extract_raw_data(startdate, loading_date)

    df_facts = transform_data(orders, order_details, products, categories, suppliers, customers_dim, artikel_dim)

    print("Shape Faktendaten:", df_facts.shape)
    print("Beispiel Faktendaten:\n", df_facts.head())

    load_facts(df_facts)

    update_loading_date(loading_date)

    print("ETL F_Einkaeufe abgeschlossen.")

if __name__ == "__main__":
    run_etl_f_einkaeufe()
