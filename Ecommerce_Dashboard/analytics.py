"""Shared analytics helpers: load the sales fact table from SQL, compute KPIs and RFM segments."""
import numpy as np
import pandas as pd

from config import VALID_STATUSES

FACT_SQL = """
SELECT oi.item_id, o.order_id, o.order_date, o.order_status, o.payment_method,
       c.customer_id, c.name AS customer_name, c.location, c.region,
       p.product_id, p.product_name, p.category, p.cost_price,
       oi.quantity, oi.unit_price, oi.discount_pct
FROM order_items oi
JOIN orders    o ON o.order_id    = oi.order_id
JOIN products  p ON p.product_id  = oi.product_id
JOIN customers c ON c.customer_id = o.customer_id
"""

SEGMENT_ORDER = ["Champions", "Loyal", "Promising", "Needs attention", "At risk", "Lost", "No valid orders"]


def load_fact(engine) -> pd.DataFrame:
    df = pd.read_sql(FACT_SQL, engine, parse_dates=["order_date"])
    df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)).round(2)
    df["profit"] = (df["revenue"] - df["quantity"] * df["cost_price"]).round(2)
    df["month"] = df["order_date"].dt.strftime("%Y-%m")
    df["is_valid"] = df["order_status"].isin(VALID_STATUSES)
    return df


def kpis(valid: pd.DataFrame) -> dict:
    revenue, profit = valid["revenue"].sum(), valid["profit"].sum()
    orders = valid["order_id"].nunique()
    return {
        "total_revenue": round(float(revenue), 2),
        "total_profit": round(float(profit), 2),
        "profit_margin_pct": round(float(profit / revenue * 100), 2),
        "total_orders": int(orders),
        "unique_customers": int(valid["customer_id"].nunique()),
        "units_sold": int(valid["quantity"].sum()),
        "avg_order_value": round(float(revenue / orders), 2),
    }


def rfm_segments(fact: pd.DataFrame, customers_all: pd.Series) -> pd.DataFrame:
    """Recency / Frequency / Monetary scoring on valid orders only.

    R and M use 5 quantile bands; F uses fixed bands (1, 2, 3, 4-5, 6+ orders) because most
    customers have very few orders and quantiles would split ties arbitrarily.
    """
    valid = fact[fact["is_valid"]]
    ref = fact["order_date"].max() + pd.Timedelta(days=1)
    g = valid.groupby("customer_id").agg(
        last_order=("order_date", "max"),
        frequency=("order_id", "nunique"),
        monetary=("revenue", "sum"),
    )
    g["recency_days"] = (ref - g["last_order"]).dt.days
    g["R"] = pd.qcut(g["recency_days"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    g["M"] = pd.qcut(g["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    g["F"] = pd.cut(g["frequency"], [0, 1, 2, 3, 5, np.inf], labels=[1, 2, 3, 4, 5]).astype(int)

    def label(r):
        if r.R >= 4 and r.F >= 4:
            return "Champions"
        if r.F >= 3 and r.R >= 3:
            return "Loyal"
        if r.R >= 4:
            return "Promising"
        if r.R <= 2 and r.F >= 3:
            return "At risk"
        if r.R <= 2:
            return "Lost"
        return "Needs attention"

    g["segment"] = g.apply(label, axis=1)
    out = pd.DataFrame({"customer_id": customers_all.values}).merge(g.reset_index(), on="customer_id", how="left")
    out["segment"] = out["segment"].fillna("No valid orders")
    return out
