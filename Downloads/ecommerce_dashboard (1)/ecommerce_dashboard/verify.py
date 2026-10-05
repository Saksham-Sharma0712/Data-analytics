"""Integrity checks. Run after the pipeline: python verify.py"""
import json
import re
import pandas as pd
from sqlalchemy import text

from config import OUT
from database import get_engine

engine = get_engine()
q = lambda sql: pd.read_sql(text(sql), engine)
checks = []


def check(name, ok):
    checks.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name)


check("no duplicate order ids", q("SELECT COUNT(*) - COUNT(DISTINCT order_id) AS d FROM orders")["d"][0] == 0)
check("no duplicate customer ids", q("SELECT COUNT(*) - COUNT(DISTINCT customer_id) AS d FROM customers")["d"][0] == 0)
check("every order has a customer", q("SELECT COUNT(*) AS n FROM orders o LEFT JOIN customers c ON c.customer_id=o.customer_id WHERE c.customer_id IS NULL")["n"][0] == 0)
check("every item has an order and a product", q("""SELECT COUNT(*) AS n FROM order_items oi
    LEFT JOIN orders o ON o.order_id=oi.order_id LEFT JOIN products p ON p.product_id=oi.product_id
    WHERE o.order_id IS NULL OR p.product_id IS NULL""")["n"][0] == 0)
check("every order has at least one item", q("SELECT COUNT(*) AS n FROM orders o WHERE o.order_id NOT IN (SELECT order_id FROM order_items)")["n"][0] == 0)
tot = q("""SELECT COUNT(*) AS n FROM orders o JOIN (
    SELECT order_id, SUM(quantity*unit_price*(1-discount_pct/100.0)) AS s FROM order_items GROUP BY order_id) t
    ON t.order_id=o.order_id WHERE ABS(o.total_amount - t.s) > 0.05""")["n"][0]
check("order totals equal the sum of their lines", tot == 0)
check("only the five expected order statuses", set(q("SELECT DISTINCT order_status s FROM orders")["s"]) <= {"Delivered", "Shipped", "Processing", "Cancelled", "Returned"})
check("emails are valid or empty", q("SELECT email FROM customers")["email"].dropna().str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$").all())

kpi = json.loads((OUT / "kpis.json").read_text())
sql_rev = q("""SELECT SUM(oi.quantity*oi.unit_price*(1-oi.discount_pct/100.0)) AS r FROM order_items oi
    JOIN orders o ON o.order_id=oi.order_id WHERE o.order_status IN ('Delivered','Shipped','Processing')""")["r"][0]
check("KPI revenue (pandas) equals revenue computed in SQL", abs(kpi["total_revenue"] - sql_rev) < 1)

html = (OUT / "dashboard.html").read_text(encoding="utf-8")
check("dashboard has embedded data", "__DATA__" not in html and '"rows":[[' in html)
print(f"\n{sum(checks)}/{len(checks)} checks passed")
raise SystemExit(0 if all(checks) else 1)
