"""
Generate draw.io ER diagrams for Business DB and DWH star schema.
Run from project root: python docs/generate_diagrams.py
Produces: docs/diagrams/erm_business_db.drawio
          docs/diagrams/erm_dwh.drawio
"""
import pathlib
import textwrap

OUT_DIR = pathlib.Path(__file__).parent / "diagrams"
OUT_DIR.mkdir(exist_ok=True)

# ── XML builders ──────────────────────────────────────────────────────────────

_cell_id = 100  # global counter for unique IDs

def _next_id() -> int:
    global _cell_id
    _cell_id += 1
    return _cell_id


def table_xml(table_id: str, name: str, columns: list[tuple[str, str]],
              x: int, y: int, w: int = 210) -> tuple[str, dict]:
    """Return (xml_string, {col_name: row_cell_id}) for a DB table entity."""
    H_HDR = 30
    H_ROW = 24
    total_h = H_HDR + H_ROW * len(columns)
    row_ids: dict[str, int] = {}
    parts: list[str] = []

    tbl_cell = _next_id()
    parts.append(
        f'<mxCell id="{tbl_cell}" value="{name}" '
        f'style="shape=table;startSize={H_HDR};container=1;collapsible=0;'
        f'childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;'
        f'align=center;resizeLast=1;fontSize=13;fillColor=#dae8fc;strokeColor=#6c8ebf;" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{total_h}" as="geometry"/>'
        f'</mxCell>'
    )

    for i, (col_name, col_type) in enumerate(columns):
        row_id   = _next_id()
        lbl_id   = _next_id()
        name_id  = _next_id()
        row_ids[col_name] = row_id
        y_off    = H_HDR + i * H_ROW
        LBL_W    = 36

        row_style = (
            "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;"
            "fillColor=none;collapsible=0;dropTarget=0;"
            "points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
            "fontSize=11;top=0;left=0;right=0;bottom=1;"
        )
        if "PK" in col_type:
            row_style += "fontStyle=1;"

        label_text = col_type if col_type in ("PK", "FK") else ""

        parts.append(
            f'<mxCell id="{row_id}" value="" style="{row_style}" vertex="1" parent="{tbl_cell}">'
            f'<mxGeometry y="{y_off}" width="{w}" height="{H_ROW}" as="geometry"/>'
            f'</mxCell>'
        )
        parts.append(
            f'<mxCell id="{lbl_id}" value="{label_text}" '
            f'style="shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;'
            f'bottom=0;right=0;fontStyle=1;fontSize=10;" vertex="1" parent="{row_id}">'
            f'<mxGeometry width="{LBL_W}" height="{H_ROW}" as="geometry">'
            f'<mxRectangle width="{LBL_W}" height="{H_ROW}" as="alternateBounds"/>'
            f'</mxGeometry></mxCell>'
        )
        parts.append(
            f'<mxCell id="{name_id}" value="{col_name}" '
            f'style="shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;'
            f'bottom=0;right=0;fontSize=11;" vertex="1" parent="{row_id}">'
            f'<mxGeometry x="{LBL_W}" width="{w - LBL_W}" height="{H_ROW}" as="geometry">'
            f'<mxRectangle width="{w - LBL_W}" height="{H_ROW}" as="alternateBounds"/>'
            f'</mxGeometry></mxCell>'
        )

    return "\n".join(parts), row_ids


def edge_xml(src_row: int, tgt_row: int, label: str = "",
             style: str = "endArrow=ERmany;endFill=0;startArrow=ERone;startFill=0;") -> str:
    eid = _next_id()
    return (
        f'<mxCell id="{eid}" value="{label}" style="{style}" '
        f'edge="1" source="{src_row}" target="{tgt_row}" parent="1">'
        f'<mxGeometry relative="1" as="geometry"/>'
        f'</mxCell>'
    )


def wrap_diagram(inner: str) -> str:
    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <mxGraphModel><root>
        <mxCell id="0"/><mxCell id="1" parent="0"/>
        {inner}
        </root></mxGraphModel>
    """)


# ── Business DB ERM ───────────────────────────────────────────────────────────

def build_business_db() -> str:
    global _cell_id
    _cell_id = 100
    parts: list[str] = []

    sup_xml, sup = table_xml("sup", "supplier", [
        ("supplier_id",   "PK"),
        ("supplier_name", ""),
        ("city",          ""),
        ("country",       ""),
    ], x=820, y=80)
    parts.append(sup_xml)

    cat_xml, cat = table_xml("cat", "category", [
        ("category_id",        "PK"),
        ("category_name",      ""),
        ("parent_category_id", "FK"),
    ], x=820, y=310)
    parts.append(cat_xml)

    pro_xml, pro = table_xml("pro", "product", [
        ("product_id",   "PK"),
        ("product_name", ""),
        ("list_price",   ""),
        ("colour",       ""),
        ("material",     ""),
        ("category_id",  "FK"),
        ("supplier_id",  "FK"),
    ], x=500, y=160)
    parts.append(pro_xml)

    cus_xml, cus = table_xml("cus", "customer", [
        ("customer_id",    "PK"),
        ("first_name",     ""),
        ("last_name",      ""),
        ("email",          ""),
        ("street_address", ""),
        ("postal_code",    ""),
        ("city",           ""),
        ("federal_state",  ""),
        ("customer_since", ""),
    ], x=40, y=40)
    parts.append(cus_xml)

    oh_xml, oh = table_xml("oh", "order_header", [
        ("order_id",       "PK"),
        ("order_date",     ""),
        ("payment_method", ""),
        ("shipping_cost",  ""),
        ("customer_id",    "FK"),
    ], x=270, y=40)
    parts.append(oh_xml)

    ol_xml, ol = table_xml("ol", "order_line", [
        ("order_line_id", "PK"),
        ("quantity",      ""),
        ("unit_price",    ""),
        ("discount",      ""),
        ("order_id",      "FK"),
        ("product_id",    "FK"),
    ], x=270, y=330)
    parts.append(ol_xml)

    # Relationships
    parts.append(edge_xml(cus["customer_id"], oh["customer_id"]))
    parts.append(edge_xml(oh["order_id"],     ol["order_id"]))
    parts.append(edge_xml(pro["product_id"],  ol["product_id"]))
    parts.append(edge_xml(cat["category_id"], pro["category_id"]))
    parts.append(edge_xml(sup["supplier_id"], pro["supplier_id"]))
    # self-referencing FK on category
    parts.append(edge_xml(
        cat["category_id"], cat["parent_category_id"],
        style="endArrow=ERmany;endFill=0;startArrow=ERone;startFill=0;exitX=1;exitY=0.5;entryX=1;entryY=0.8;"
    ))

    return wrap_diagram("\n".join(parts))


# ── DWH Star Schema ───────────────────────────────────────────────────────────

def build_dwh() -> str:
    global _cell_id
    _cell_id = 200
    parts: list[str] = []

    fact_xml, fact = table_xml("fact", "fact_sales", [
        ("sales_sk",        "PK"),
        ("date_sk",         "FK"),
        ("customer_sk",     "FK"),
        ("product_sk",      "FK"),
        ("supplier_sk",     "FK"),
        ("order_id",        ""),
        ("quantity",        ""),
        ("gross_amount",    ""),
        ("discount_amount", ""),
        ("net_amount",      ""),
        ("shipping_cost",   ""),
    ], x=350, y=220, w=220)
    parts.append(fact_xml)

    ddate_xml, ddate = table_xml("ddate", "dim_date", [
        ("date_sk",       "PK"),
        ("full_date",     ""),
        ("day",           ""),
        ("month",         ""),
        ("month_name",    ""),
        ("quarter",       ""),
        ("year",          ""),
        ("weekday",       ""),
        ("weekday_name",  ""),
        ("calendar_week", ""),
    ], x=350, y=20, w=200)
    parts.append(ddate_xml)

    dcus_xml, dcus = table_xml("dcus", "dim_customer", [
        ("customer_sk",   "PK"),
        ("customer_id",   ""),
        ("first_name",    ""),
        ("last_name",     ""),
        ("email",         ""),
        ("street_address",""),
        ("postal_code",   ""),
        ("plz_region",    ""),
        ("plz_zone",      ""),
        ("city",          ""),
        ("federal_state", ""),
        ("valid_from",    ""),
        ("valid_to",      ""),
        ("is_current",    ""),
    ], x=20, y=150, w=210)
    parts.append(dcus_xml)

    dpro_xml, dpro = table_xml("dpro", "dim_product", [
        ("product_sk",        "PK"),
        ("product_id",        ""),
        ("product_name",      ""),
        ("colour",            ""),
        ("material",          ""),
        ("list_price",        ""),
        ("category_name",     ""),
        ("top_category_name", ""),
    ], x=680, y=150, w=210)
    parts.append(dpro_xml)

    dsup_xml, dsup = table_xml("dsup", "dim_supplier", [
        ("supplier_sk",   "PK"),
        ("supplier_id",   ""),
        ("supplier_name", ""),
        ("city",          ""),
        ("country",       ""),
    ], x=350, y=580, w=200)
    parts.append(dsup_xml)

    # Relationships: dim → fact
    edge_style = "endArrow=ERone;endFill=0;startArrow=ERmany;startFill=0;"
    parts.append(edge_xml(ddate["date_sk"],     fact["date_sk"],     style=edge_style))
    parts.append(edge_xml(dcus["customer_sk"],  fact["customer_sk"], style=edge_style))
    parts.append(edge_xml(dpro["product_sk"],   fact["product_sk"],  style=edge_style))
    parts.append(edge_xml(dsup["supplier_sk"],  fact["supplier_sk"], style=edge_style))

    return wrap_diagram("\n".join(parts))


# ── Write files ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bdb = OUT_DIR / "erm_business_db.drawio"
    dwh = OUT_DIR / "erm_dwh.drawio"

    bdb.write_text(build_business_db(), encoding="utf-8")
    print(f"Written: {bdb}")

    dwh.write_text(build_dwh(), encoding="utf-8")
    print(f"Written: {dwh}")
