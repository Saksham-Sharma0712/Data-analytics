"""Step 2 - Data cleaning & preprocessing (Pandas).

Reads data/raw/*.csv, fixes quality problems and writes data/clean/*.csv plus a
cleaning_report.json that records exactly what was changed.
"""
import json
import re
import pandas as pd

from config import RAW, CLEAN, CITY_REGION, ALL_STATUSES, PAYMENT_METHODS

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CITY_ALIASES = {"Bangalore": "Bengaluru"}
PAY_MAP = {
    "upi": "UPI", "credit card": "Credit Card", "debit card": "Debit Card",
    "cod": "Cash on Delivery", "cash on delivery": "Cash on Delivery",
    "net banking": "Net Banking", "netbanking": "Net Banking",
}


def clean_customers(df, rep):
    rep["customers_raw_rows"] = len(df)
    df = df.drop_duplicates().drop_duplicates("customer_id")
    rep["customers_duplicates_removed"] = rep["customers_raw_rows"] - len(df)

    city = df["location"].astype("string").str.strip().str.title().replace(CITY_ALIASES)
    rep["customers_missing_city_filled_unknown"] = int(city.isna().sum())
    df["location"] = city.fillna("Unknown")
    df["region"] = df["location"].map(CITY_REGION).fillna("Unknown")

    email = df["email"].astype("string").str.strip().str.lower()
    bad = email.notna() & ~email.fillna("").str.match(EMAIL_RE)
    rep["customers_invalid_email_nulled"] = int(bad.sum())
    rep["customers_missing_email"] = int(email.isna().sum())
    df["email"] = email.mask(bad)

    df["name"] = df["name"].str.strip()
    df["registration_date"] = pd.to_datetime(df["registration_date"], errors="coerce")
    df = df.dropna(subset=["registration_date"])
    return df[["customer_id", "name", "email", "location", "region", "registration_date"]].reset_index(drop=True)


def clean_products(df, rep):
    df = df.drop_duplicates("product_id").copy()
    missing = int(df["stock_quantity"].isna().sum())
    rep["products_missing_stock_filled_median"] = missing
    df["stock_quantity"] = df["stock_quantity"].fillna(df["stock_quantity"].median()).astype(int)
    assert (df["price"] > 0).all() and (df["cost_price"] > 0).all(), "non-positive price found"
    return df.reset_index(drop=True)


def clean_items(df, orders_ids, product_ids, rep):
    n0 = len(df)
    df = df.drop_duplicates().drop_duplicates(["order_id", "product_id"])
    rep["order_items_duplicates_removed"] = n0 - len(df)
    n1 = len(df)
    df = df[df["order_id"].isin(orders_ids) & df["product_id"].isin(product_ids) & (df["quantity"] > 0)]
    rep["order_items_orphans_or_invalid_removed"] = n1 - len(df)
    return df.reset_index(drop=True)


def clean_orders(df, customer_ids, items, rep):
    n0 = len(df)
    df = df.drop_duplicates().drop_duplicates("order_id").copy()
    rep["orders_duplicates_removed"] = n0 - len(df)

    # standardise categorical text
    df["order_status"] = df["order_status"].str.strip().str.title()
    unknown_status = ~df["order_status"].isin(ALL_STATUSES)
    rep["orders_unknown_status_removed"] = int(unknown_status.sum())
    df = df[~unknown_status]

    pay = df["payment_method"].str.strip().str.lower().map(PAY_MAP)
    rep["orders_unknown_payment_set_other"] = int(pay.isna().sum())
    df["payment_method"] = pay.fillna("Other")

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    rep["orders_invalid_date_removed"] = int(df["order_date"].isna().sum())
    df = df.dropna(subset=["order_date"])

    n1 = len(df)
    df = df[df["customer_id"].isin(customer_ids)]
    rep["orders_orphan_customer_removed"] = n1 - len(df)

    # total_amount is recomputed from order lines so it is always consistent
    line_total = (items["quantity"] * items["unit_price"] * (1 - items["discount_pct"] / 100))
    calc = line_total.groupby(items["order_id"]).sum().round(2)
    df["calc_total"] = df["order_id"].map(calc)
    rep["orders_total_missing_recomputed"] = int(df["total_amount"].isna().sum())
    mismatch = df["total_amount"].notna() & ((df["total_amount"] - df["calc_total"]).abs() > 0.01)
    rep["orders_total_mismatch_recomputed"] = int(mismatch.sum())
    no_items = df["calc_total"].isna()
    rep["orders_without_items_removed"] = int(no_items.sum())
    df = df[~no_items]
    df["total_amount"] = df["calc_total"]
    df = df.drop(columns="calc_total")
    return df[["order_id", "customer_id", "order_date", "order_status", "payment_method", "total_amount"]].reset_index(drop=True)


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    raw = {n: pd.read_csv(RAW / f"{n}.csv") for n in ["customers", "products", "orders", "order_items"]}
    rep = {}

    customers = clean_customers(raw["customers"], rep)
    products = clean_products(raw["products"], rep)
    # items are cleaned against raw order ids first, then orders are reconciled against clean items
    items = clean_items(raw["order_items"], set(raw["orders"]["order_id"]), set(products["product_id"]), rep)
    orders = clean_orders(raw["orders"], set(customers["customer_id"]), items, rep)
    items = items[items["order_id"].isin(orders["order_id"])].reset_index(drop=True)

    for name, df in [("customers", customers), ("products", products), ("orders", orders), ("order_items", items)]:
        df.to_csv(CLEAN / f"{name}.csv", index=False)
        rep[f"{name}_clean_rows"] = len(df)

    (CLEAN / "cleaning_report.json").write_text(json.dumps(rep, indent=2))
    print("Cleaning report")
    for k, v in rep.items():
        print(f"  {k:<48}{v:>8,}")


if __name__ == "__main__":
    main()
