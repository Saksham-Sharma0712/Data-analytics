"""Step 1 - Data collection.

Generates a realistic *synthetic* e-commerce dataset (customers, products, orders,
order items) and writes it to data/raw/. The raw files are deliberately messy
(duplicates, missing values, inconsistent spelling) so the cleaning step has real work.

Swap this script for a real export (Shopify, WooCommerce, ...) as long as the CSVs
keep the same columns.
"""
import numpy as np
import pandas as pd
from datetime import date

from config import RAW, CITY_REGION, ALL_STATUSES, PAYMENT_METHODS

SEED = 42
N_CUSTOMERS = 1200
N_ORDERS = 6500
START, END = date(2025, 1, 1), date(2026, 9, 30)

# category -> (cost ratio of selling price, [(product, price in INR), ...])
CATALOG = {
    "Electronics": (0.72, [("Wireless Earbuds", 2499), ("Bluetooth Speaker", 3299), ("Smartwatch", 5999),
                           ("Power Bank 20000mAh", 1799), ("Gaming Mouse", 1499), ("Mechanical Keyboard", 3499),
                           ("HD Webcam", 2199), ("USB-C Hub", 1299)]),
    "Fashion": (0.55, [("Cotton T-Shirt", 599), ("Slim Fit Jeans", 1799), ("Running Shoes", 2999),
                       ("Leather Wallet", 899), ("Hoodie", 1599), ("Kurta Set", 1999),
                       ("Sunglasses", 1299), ("Laptop Backpack", 1699)]),
    "Home & Kitchen": (0.62, [("Air Fryer", 5499), ("Non-stick Cookware Set", 2799), ("Mixer Grinder", 3299),
                              ("Cotton Bedsheet Set", 1299), ("LED Desk Lamp", 899), ("Steel Water Bottle", 599),
                              ("Vacuum Cleaner", 6999), ("Storage Containers", 799)]),
    "Beauty": (0.42, [("Vitamin C Serum", 699), ("Sunscreen SPF 50", 449), ("Hair Dryer", 1599),
                      ("Perfume 100ml", 1899), ("Face Wash", 249), ("Beard Trimmer", 1299),
                      ("Lipstick Set", 799), ("Body Lotion", 399)]),
    "Sports & Fitness": (0.58, [("Yoga Mat", 899), ("Dumbbell Set 10kg", 1999), ("Cricket Bat", 2499),
                                ("Badminton Racket", 1299), ("Resistance Bands", 499), ("Fitness Tracker", 2999),
                                ("Football", 799), ("Skipping Rope", 299)]),
    "Books & Stationery": (0.78, [("Python Programming Book", 649), ("Data Analysis Handbook", 799), ("Notebook Pack of 5", 349),
                                  ("Gel Pen Set", 199), ("Desk Organizer", 549), ("Planner 2026", 399),
                                  ("Sketchbook A4", 299), ("Scientific Calculator", 999)]),
}

FIRST = ["Aarav", "Vivaan", "Aditya", "Arjun", "Rohan", "Karan", "Ishaan", "Rahul", "Siddharth", "Manish",
         "Ananya", "Diya", "Priya", "Neha", "Kavya", "Riya", "Sneha", "Pooja", "Meera", "Isha"]
LAST = ["Sharma", "Verma", "Gupta", "Singh", "Patel", "Mehta", "Jain", "Agarwal", "Reddy", "Nair",
        "Iyer", "Das", "Khan", "Chopra", "Bansal", "Saxena", "Joshi", "Rathore", "Shekhawat", "Malhotra"]


def build_clean_tables(rng: np.random.Generator):
    # ---- products -------------------------------------------------------
    rows, pid = [], 1
    for cat, (cost_ratio, items) in CATALOG.items():
        for name, price in items:
            cost = round(price * cost_ratio * rng.uniform(0.93, 1.07), 2)
            rows.append((pid, name, cat, float(price), cost, int(rng.integers(0, 500))))
            pid += 1
    products = pd.DataFrame(rows, columns=["product_id", "product_name", "category", "price", "cost_price", "stock_quantity"])
    pop = rng.lognormal(0, 0.8, len(products))
    pop = pop / pop.sum()

    # ---- customers ------------------------------------------------------
    cities = list(CITY_REGION)
    city_p = np.array([14, 16, 7, 5, 15, 8, 6, 12, 8, 7, 6, 4], dtype=float)
    city_p /= city_p.sum()
    reg_days = pd.date_range("2024-01-01", "2026-08-31")
    names = []
    for i in range(N_CUSTOMERS):
        names.append(f"{rng.choice(FIRST)} {rng.choice(LAST)}")
    customers = pd.DataFrame({
        "customer_id": np.arange(1, N_CUSTOMERS + 1),
        "name": names,
        "location": rng.choice(cities, N_CUSTOMERS, p=city_p),
        "registration_date": rng.choice(reg_days, N_CUSTOMERS),
    })
    customers["email"] = [
        f"{n.lower().replace(' ', '.')}{cid}@{rng.choice(['gmail.com', 'outlook.com', 'yahoo.in', 'proton.me'])}"
        for n, cid in zip(customers["name"], customers["customer_id"])
    ]
    customers["registration_date"] = pd.to_datetime(customers["registration_date"])
    customers = customers[["customer_id", "name", "email", "location", "registration_date"]]

    # ---- orders & order items -------------------------------------------
    days = pd.date_range(START, END)
    t = np.arange(len(days)) / len(days)
    w = 1 + 0.6 * t                                   # business grows over time
    m = days.month.values
    w = w * np.where(np.isin(m, [10, 11]), 1.8, 1.0)  # festive season
    w = w * np.where(m == 12, 1.3, 1.0)
    w = w * np.where(days.dayofweek.values >= 5, 1.15, 1.0)  # weekends

    activity = rng.gamma(0.6, 1.0, N_CUSTOMERS) + 0.02    # heavy-tailed: few power buyers
    activity /= activity.sum()
    cust_for_order = rng.choice(customers["customer_id"].values, N_ORDERS, p=activity)
    reg_lookup = customers.set_index("customer_id")["registration_date"]

    orders, items, item_id = [], [], 1
    for oid, cid in enumerate(cust_for_order, start=1001):
        start_idx = int(days.searchsorted(reg_lookup[cid]))
        start_idx = min(start_idx, len(days) - 1)
        p = w[start_idx:] / w[start_idx:].sum()
        odate = days[start_idx:][rng.choice(len(p), p=p)]

        n_lines = rng.choice([1, 2, 3, 4], p=[0.5, 0.3, 0.15, 0.05])
        pids = rng.choice(products["product_id"].values, n_lines, replace=False, p=pop)
        total = 0.0
        for pr in pids:
            price = float(products.loc[products["product_id"] == pr, "price"].iat[0])
            qty = int(rng.choice([1, 2, 3], p=[0.75, 0.18, 0.07]))
            disc = int(rng.choice([0, 5, 10, 15, 20], p=[0.45, 0.2, 0.2, 0.1, 0.05]))
            total += qty * price * (1 - disc / 100)
            items.append((item_id, oid, int(pr), qty, price, disc))
            item_id += 1

        if (END - odate.date()).days < 7:
            status = rng.choice(["Processing", "Shipped"], p=[0.5, 0.5])
        else:
            status = rng.choice(ALL_STATUSES, p=[0.80, 0.0, 0.0, 0.11, 0.09])
        pay = rng.choice(PAYMENT_METHODS, p=[0.42, 0.22, 0.15, 0.14, 0.07])
        orders.append((oid, int(cid), odate, status, pay, round(total, 2)))

    orders = pd.DataFrame(orders, columns=["order_id", "customer_id", "order_date", "order_status",
                                           "payment_method", "total_amount"])
    items = pd.DataFrame(items, columns=["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_pct"])
    return customers, products, orders, items


def make_messy(customers, products, orders, items, rng):
    """Inject the kinds of problems real exports have."""
    c, p, o, i = customers.copy(), products.copy(), orders.copy(), items.copy()

    # customers: inconsistent city spelling / casing / whitespace
    c["location"] = c["location"].astype(object)
    blr = (c["location"] == "Bengaluru") & (rng.random(len(c)) < 0.3)
    c.loc[blr, "location"] = "Bangalore"
    for idx in rng.choice(c.index, int(len(c) * 0.12), replace=False):
        v = c.at[idx, "location"]
        c.at[idx, "location"] = rng.choice([v.lower(), v.upper(), f" {v} ", f"{v} "])
    c.loc[rng.choice(c.index, 24, replace=False), "location"] = np.nan            # missing city
    c["email"] = c["email"].astype(object)
    c.loc[rng.choice(c.index, 36, replace=False), "email"] = np.nan               # missing email
    c.loc[rng.choice(c.index, 8, replace=False), "email"] = "not-an-email.com"     # invalid email
    c = pd.concat([c, c.sample(15, random_state=1)], ignore_index=True)           # duplicates

    # products: missing stock
    p["stock_quantity"] = p["stock_quantity"].astype("float")
    p.loc[rng.choice(p.index, 2, replace=False), "stock_quantity"] = np.nan

    # orders: status / payment spelling, missing totals, duplicates
    for idx in rng.choice(o.index, int(len(o) * 0.10), replace=False):
        v = o.at[idx, "order_status"]
        o.at[idx, "order_status"] = rng.choice([v.lower(), v.upper(), f"{v} "])
    pay_variants = {"UPI": ["upi", "Upi"], "Credit Card": ["credit card", "CREDIT CARD"],
                    "Debit Card": ["debit card"], "Cash on Delivery": ["COD", "cash on delivery"],
                    "Net Banking": ["net banking", "NetBanking"]}
    for idx in rng.choice(o.index, int(len(o) * 0.10), replace=False):
        v = o.at[idx, "payment_method"]
        o.at[idx, "payment_method"] = rng.choice(pay_variants[v])
    o.loc[rng.choice(o.index, 40, replace=False), "total_amount"] = np.nan
    o = pd.concat([o, o.sample(60, random_state=2)], ignore_index=True)

    # order items: duplicated lines
    i = pd.concat([i, i.sample(25, random_state=3)], ignore_index=True)
    return c, p, o, i


def main():
    rng = np.random.default_rng(SEED)
    RAW.mkdir(parents=True, exist_ok=True)
    tables = build_clean_tables(rng)
    c, p, o, i = make_messy(*tables, rng)
    for name, df in [("customers", c), ("products", p), ("orders", o), ("order_items", i)]:
        df.to_csv(RAW / f"{name}.csv", index=False)
        print(f"  raw/{name}.csv  {len(df):>6,} rows")
    print("Raw data written to", RAW)


if __name__ == "__main__":
    main()
