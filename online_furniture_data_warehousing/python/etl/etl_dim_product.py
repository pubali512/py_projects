"""
ETL_DimProduct.py -- Dimension: DIM_Product  (SCD Type 1)
Reads products and their category hierarchy from RAW staging tables,
flattens sub-category -> top-category, and upserts into DIM_Product.
Changed attributes are overwritten (SCD 1 -- no history).
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect, PLACEHOLDER


def extract_dim_product(conn) -> list:
    """Join RAW products with category hierarchy to resolve top-category name."""
    return conn.execute("""
        SELECT p.ProductId,
               p.ProductName,
               p.Colour,
               p.Material,
               p.ListPrice,
               c.CategoryName,
               COALESCE(top.CategoryName, c.CategoryName) AS TopCategoryName
        FROM RAW_BusinessDB_Product   p
        JOIN RAW_BusinessDB_Category  c   ON p.CategoryId    = c.CategoryId
        LEFT JOIN RAW_BusinessDB_Category top
                                          ON c.ParentCategoryId = top.CategoryId
    """).fetchall()


def transform_dim_product(raw_rows: list) -> list[tuple]:
    """Return product tuples ready for upsert (no filtering needed -- handled in load)."""
    return [
        (r["ProductId"], r["ProductName"], r["Colour"], r["Material"],
         r["ListPrice"], r["CategoryName"], r["TopCategoryName"])
        for r in raw_rows
    ]


def load_dim_product(conn, rows: list[tuple]) -> tuple[int, int]:
    """Insert new products; overwrite changed attributes for existing ones (SCD 1).
    Returns (inserted_count, updated_count).
    """
    existing = {
        r[0]: r
        for r in conn.execute(
            "SELECT ProductId, ProductName, Colour, Material, "
            "ListPrice, CategoryName, TopCategoryName FROM DIM_Product"
        )
    }
    inserted = updated = 0
    for (pid, name, Colour, Material, price, cat, top_cat) in rows:
        if pid not in existing:
            conn.execute(
                f"INSERT INTO DIM_Product "
                f"(ProductId, ProductName, Colour, Material, ListPrice, "
                f"CategoryName, TopCategoryName) VALUES ({','.join([PLACEHOLDER]*7)})",
                (pid, name, Colour, Material, price, cat, top_cat),
            )
            inserted += 1
        else:
            ex = existing[pid]
            if (ex[1], ex[2], ex[3], ex[4], ex[5], ex[6]) != (name, Colour, Material, price, cat, top_cat):
                conn.execute(
                    f"UPDATE DIM_Product SET ProductName={PLACEHOLDER}, Colour={PLACEHOLDER}, "
                    f"Material={PLACEHOLDER}, ListPrice={PLACEHOLDER}, "
                    f"CategoryName={PLACEHOLDER}, TopCategoryName={PLACEHOLDER} "
                    f"WHERE ProductId={PLACEHOLDER}",
                    (name, Colour, Material, price, cat, top_cat, pid),
                )
                updated += 1
    conn.commit()
    return inserted, updated


def run_etl_dim_product() -> None:
    conn = connect()
    try:
        raw = extract_dim_product(conn)
        rows = transform_dim_product(raw)
        inserted, updated = load_dim_product(conn, rows)
        print(f"  [DimProduct]  {inserted:>6,} inserted, {updated:>4,} updated (SCD1)")
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl_dim_product()
