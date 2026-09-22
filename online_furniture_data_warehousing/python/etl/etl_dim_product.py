"""
ETL_DimProduct.py -- Dimension: dim_product  (SCD Type 1)
Reads products and their category hierarchy from RAW staging tables,
flattens sub-category -> top-category, and upserts into dim_product.
Changed attributes are overwritten (SCD 1 -- no history).
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from db import connect, PLACEHOLDER


def extract_dim_product(conn) -> list:
    """Join RAW products with category hierarchy to resolve top-category name."""
    return conn.execute("""
        SELECT p.product_id,
               p.product_name,
               p.colour,
               p.material,
               p.list_price,
               c.category_name,
               COALESCE(top.category_name, c.category_name) AS top_category_name
        FROM RAW_BusinessDB_Product   p
        JOIN RAW_BusinessDB_Category  c   ON p.category_id    = c.category_id
        LEFT JOIN RAW_BusinessDB_Category top
                                          ON c.parent_category_id = top.category_id
    """).fetchall()


def transform_dim_product(raw_rows: list) -> list[tuple]:
    """Return product tuples ready for upsert (no filtering needed -- handled in load)."""
    return [
        (r["product_id"], r["product_name"], r["colour"], r["material"],
         r["list_price"], r["category_name"], r["top_category_name"])
        for r in raw_rows
    ]


def load_dim_product(conn, rows: list[tuple]) -> tuple[int, int]:
    """Insert new products; overwrite changed attributes for existing ones (SCD 1).
    Returns (inserted_count, updated_count).
    """
    existing = {
        r[0]: r
        for r in conn.execute(
            "SELECT product_id, product_name, colour, material, "
            "list_price, category_name, top_category_name FROM dim_product"
        )
    }
    inserted = updated = 0
    for (pid, name, colour, material, price, cat, top_cat) in rows:
        if pid not in existing:
            conn.execute(
                f"INSERT INTO dim_product "
                f"(product_id, product_name, colour, material, list_price, "
                f"category_name, top_category_name) VALUES ({','.join([PLACEHOLDER]*7)})",
                (pid, name, colour, material, price, cat, top_cat),
            )
            inserted += 1
        else:
            ex = existing[pid]
            if (ex[1], ex[2], ex[3], ex[4], ex[5], ex[6]) != (name, colour, material, price, cat, top_cat):
                conn.execute(
                    f"UPDATE dim_product SET product_name={PLACEHOLDER}, colour={PLACEHOLDER}, "
                    f"material={PLACEHOLDER}, list_price={PLACEHOLDER}, "
                    f"category_name={PLACEHOLDER}, top_category_name={PLACEHOLDER} "
                    f"WHERE product_id={PLACEHOLDER}",
                    (name, colour, material, price, cat, top_cat, pid),
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
