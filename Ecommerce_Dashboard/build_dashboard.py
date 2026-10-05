"""Step 5 - Build the interactive dashboard (output/dashboard.html).

Pulls the sales fact table from the database, adds RFM customer segments and embeds a compact
copy of the data into dashboard_template.html. The result is ONE self-contained file: open it in
any browser, no server needed (it loads Chart.js from a CDN, so an internet connection is required).
"""
import json
import pandas as pd

from analytics import SEGMENT_ORDER, load_fact, rfm_segments
from config import ALL_STATUSES, OUT, ROOT, VALID_STATUSES
from database import get_engine


def build_payload(engine) -> dict:
    fact = load_fact(engine).sort_values(["order_date", "item_id"]).reset_index(drop=True)
    customers = pd.read_sql("SELECT customer_id, name, location FROM customers", engine)
    rfm = rfm_segments(fact, customers["customer_id"]).set_index("customer_id")["segment"]

    months = sorted(fact["month"].unique())
    cats = sorted(fact["category"].unique())
    prods = fact[["product_id", "product_name", "category"]].drop_duplicates().sort_values(["category", "product_name"])
    regions = sorted(fact["region"].unique())
    payments = sorted(fact["payment_method"].unique())

    m_ix = {v: i for i, v in enumerate(months)}
    c_ix = {v: i for i, v in enumerate(cats)}
    p_ix = {pid: i for i, pid in enumerate(prods["product_id"])}
    r_ix = {v: i for i, v in enumerate(regions)}
    s_ix = {v: i for i, v in enumerate(ALL_STATUSES)}
    pay_ix = {v: i for i, v in enumerate(payments)}
    cust_ids = sorted(fact["customer_id"].unique())
    cu_ix = {v: i for i, v in enumerate(cust_ids)}
    cinfo = customers.set_index("customer_id")

    rows = [[m_ix[r.month], p_ix[r.product_id], r_ix[r.region], s_ix[r.order_status], pay_ix[r.payment_method],
             cu_ix[r.customer_id], int(r.order_id), int(r.quantity), float(r.revenue), float(r.profit)]
            for r in fact.itertuples()]

    return {
        "meta": {"currency": "INR", "from": str(fact["order_date"].min().date()), "to": str(fact["order_date"].max().date())},
        "months": months,
        "categories": cats,
        "products": [{"n": r.product_name, "c": c_ix[r.category]} for r in prods.itertuples()],
        "regions": regions,
        "statuses": ALL_STATUSES,
        "defaultStatuses": [s_ix[s] for s in VALID_STATUSES],
        "payments": payments,
        "segments": SEGMENT_ORDER,
        "customers": [{"n": cinfo.at[c, "name"], "l": cinfo.at[c, "location"],
                       "s": SEGMENT_ORDER.index(rfm.loc[c])} for c in cust_ids],
        "rows": rows,
    }


def main():
    payload = build_payload(get_engine())
    template = (ROOT / "dashboard_template.html").read_text(encoding="utf-8")
    html = template.replace("__DATA__", json.dumps(payload, separators=(",", ":")))
    OUT.mkdir(exist_ok=True)
    target = OUT / "dashboard.html"
    target.write_text(html, encoding="utf-8")
    (OUT / "index.html").write_text(html, encoding="utf-8")   # index.html lets static hosts (Render) serve it at "/"
    print(f"Dashboard written: {target}  ({target.stat().st_size / 1024:,.0f} KB, {len(payload['rows']):,} rows)")


if __name__ == "__main__":
    main()
