"""Step 4 - Exploratory data analysis, KPI calculation and report export.

Reads from the database, prints an EDA summary and writes:
  output/kpis.json
  output/ecommerce_analysis.xlsx   (one sheet per analysis)
  output/csv/*.csv                 (same tables as CSV)
  output/powerbi/*.csv             (flat tables ready to import into Power BI)
"""
import json
import pandas as pd

from analytics import SEGMENT_ORDER, kpis, load_fact, rfm_segments
from config import OUT
from database import get_engine


def build_tables(fact: pd.DataFrame, customers: pd.DataFrame) -> dict:
    valid = fact[fact["is_valid"]]

    monthly = valid.groupby("month").agg(
        revenue=("revenue", "sum"), profit=("profit", "sum"),
        orders=("order_id", "nunique"), units=("quantity", "sum")).reset_index()
    monthly["aov"] = (monthly["revenue"] / monthly["orders"]).round(2)
    monthly["revenue_mom_pct"] = (monthly["revenue"].pct_change() * 100).round(1)

    category = valid.groupby("category").agg(
        revenue=("revenue", "sum"), profit=("profit", "sum"),
        orders=("order_id", "nunique"), units=("quantity", "sum")).reset_index()
    category["margin_pct"] = (category["profit"] / category["revenue"] * 100).round(1)
    category["revenue_share_pct"] = (category["revenue"] / category["revenue"].sum() * 100).round(1)
    category = category.sort_values("revenue", ascending=False)

    product = valid.groupby(["product_id", "product_name", "category"]).agg(
        revenue=("revenue", "sum"), profit=("profit", "sum"), units=("quantity", "sum")).reset_index()
    product["margin_pct"] = (product["profit"] / product["revenue"] * 100).round(1)
    product = product.sort_values("revenue", ascending=False)
    product["rank"] = range(1, len(product) + 1)

    region = valid.groupby("region").agg(
        revenue=("revenue", "sum"), orders=("order_id", "nunique"),
        customers=("customer_id", "nunique")).reset_index().sort_values("revenue", ascending=False)

    payment = valid.groupby("payment_method").agg(
        orders=("order_id", "nunique"), revenue=("revenue", "sum")).reset_index().sort_values("orders", ascending=False)

    status = fact.groupby("order_status")["order_id"].nunique().rename("orders").reset_index()
    status["share_pct"] = (status["orders"] / status["orders"].sum() * 100).round(1)

    rfm = rfm_segments(fact, customers["customer_id"])
    rfm = rfm.merge(customers[["customer_id", "name", "location", "region"]], on="customer_id")
    seg = rfm.groupby("segment").agg(customers=("customer_id", "count"), revenue=("monetary", "sum"),
                                     avg_orders=("frequency", "mean")).reset_index()
    seg["segment"] = pd.Categorical(seg["segment"], SEGMENT_ORDER, ordered=True)
    seg = seg.sort_values("segment")
    seg["avg_orders"] = seg["avg_orders"].fillna(0).round(2)
    seg["revenue"] = seg["revenue"].fillna(0).round(2)

    top_customers = rfm.sort_values("monetary", ascending=False).head(20)[
        ["customer_id", "name", "location", "frequency", "monetary", "recency_days", "segment"]]

    for df in (monthly, category, product, region, payment):
        for col in df.select_dtypes("float").columns:
            df[col] = df[col].round(2)

    return {"monthly_sales": monthly, "category_performance": category, "product_performance": product,
            "regional_sales": region, "payment_mix": payment, "order_status_mix": status,
            "customer_segments": seg, "top_customers": top_customers, "_rfm": rfm}


def main():
    engine = get_engine()
    fact = load_fact(engine)
    customers = pd.read_sql("SELECT customer_id, name, location, region FROM customers", engine)
    valid = fact[fact["is_valid"]]

    print("=== EDA ===")
    print(f"line items: {len(fact):,}   orders: {fact['order_id'].nunique():,}   "
          f"period: {fact['order_date'].min().date()} -> {fact['order_date'].max().date()}")
    print("missing values per column:\n", fact.isna().sum()[lambda s: s > 0].to_string() or "  none")
    print("order status share (%):\n", (fact.drop_duplicates('order_id')['order_status'].value_counts(normalize=True) * 100).round(1).to_string())
    print("revenue per line item:\n", fact["revenue"].describe().round(1).to_string())

    k = kpis(valid)
    print("\n=== KPIs (valid orders: Delivered / Shipped / Processing) ===")
    for key, v in k.items():
        print(f"  {key:<20}{v:>16,.2f}")

    t = build_tables(fact, customers)
    rfm = t.pop("_rfm")

    OUT.mkdir(exist_ok=True)
    (OUT / "csv").mkdir(exist_ok=True)
    (OUT / "powerbi").mkdir(exist_ok=True)
    (OUT / "kpis.json").write_text(json.dumps(k, indent=2))

    with pd.ExcelWriter(OUT / "ecommerce_analysis.xlsx", engine="openpyxl") as xl:
        pd.DataFrame(list(k.items()), columns=["kpi", "value"]).to_excel(xl, sheet_name="KPIs", index=False)
        for name, df in t.items():
            df.to_excel(xl, sheet_name=name[:31], index=False)
            df.to_csv(OUT / "csv" / f"{name}.csv", index=False)
        for ws in xl.book.worksheets:                      # simple column auto-width
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(40, max(len(str(c.value or "")) for c in col) + 2)

    # Power BI files: one flat fact table + a customer dimension carrying the RFM segment
    pbi = fact.merge(rfm[["customer_id", "segment"]], on="customer_id").rename(columns={"segment": "customer_segment"})
    pbi = pbi[["item_id", "order_id", "order_date", "month", "order_status", "is_valid", "payment_method", "customer_id",
               "customer_name", "location", "region", "customer_segment", "product_id", "product_name", "category",
               "quantity", "unit_price", "discount_pct", "cost_price", "revenue", "profit"]]
    pbi.to_csv(OUT / "powerbi" / "fact_sales.csv", index=False)
    rfm.to_csv(OUT / "powerbi" / "dim_customer_rfm.csv", index=False)

    print("\nTop categories:\n", t["category_performance"][["category", "revenue", "margin_pct"]].to_string(index=False))
    print("\nSegments:\n", t["customer_segments"].to_string(index=False))
    print("\nWrote Excel + CSV reports to", OUT)


if __name__ == "__main__":
    main()
