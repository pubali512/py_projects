"""
Database connection abstraction.
All scripts import from here — to switch databases, change only this file.

Current backend: SQLite
To migrate to MSSQL: replace connect() body with pyodbc.connect() and update
the placeholder constant (PLACEHOLDER = "%s").
"""

import sqlite3
import pathlib

# SQLite: single-file database stored alongside the data assets
DB_PATH = pathlib.Path(__file__).parent.parent / "data" / "furniture.db"

# SQL parameter placeholder — "?" for sqlite3, "%s" for pyodbc/psycopg2
PLACEHOLDER = "?"


def connect() -> sqlite3.Connection:
    """Return an open database connection with FK enforcement enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # access columns by name: row["customer_id"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
