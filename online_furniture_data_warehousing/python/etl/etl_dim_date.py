"""
ETL_DimDate.py — Dimension: dim_date
Reads distinct order dates from RAW_BusinessDB_OrderHeader,
derives date attributes, and loads new rows into dim_date.
"""

import pathlib
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect, PLACEHOLDER


# ── Static lookup helpers ─────────────────────────────────────────────────────

_MONTH_NAMES = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]
_WEEKDAY_NAMES = [
    "Montag", "Dienstag", "Mittwoch", "Donnerstag",
    "Freitag", "Samstag", "Sonntag",
]


def extract_dim_date(conn) -> list:
    """Return all distinct order dates from the RAW staging table."""
    return conn.execute(
        "SELECT DISTINCT order_date FROM RAW_BusinessDB_OrderHeader"
    ).fetchall()


def transform_dim_date(raw_rows: list, existing_sk: set) -> list[tuple]:
    """Derive date dimension attributes; skip dates that already exist in dim_date."""
    rows = []
    for (order_date,) in raw_rows:
        sk = int(order_date.replace("-", ""))
        if sk in existing_sk:
            continue
        d = date.fromisoformat(order_date)
        rows.append((
            sk,
            order_date,
            d.day,
            d.month,
            _MONTH_NAMES[d.month - 1],
            (d.month - 1) // 3 + 1,
            d.year,
            d.weekday(),
            _WEEKDAY_NAMES[d.weekday()],
            d.isocalendar()[1],
        ))
    return rows


def load_dim_date(conn, rows: list[tuple]) -> int:
    """Insert new date rows into dim_date; returns count of inserted rows."""
    if rows:
        conn.executemany(
            f"INSERT INTO dim_date VALUES ({','.join([PLACEHOLDER] * 10)})",
            rows,
        )
        conn.commit()
    return len(rows)


def run_etl_dim_date() -> None:
    conn = connect()
    try:
        existing_sk = {r[0] for r in conn.execute("SELECT date_sk FROM dim_date")}
        raw = extract_dim_date(conn)
        rows = transform_dim_date(raw, existing_sk)
        n = load_dim_date(conn, rows)
        print(f"  [DimDate]     {n:>6,} new rows inserted")
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl_dim_date()
