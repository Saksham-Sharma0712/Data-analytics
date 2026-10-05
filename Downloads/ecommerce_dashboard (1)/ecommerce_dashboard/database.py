"""Database layer (SQLAlchemy). SQLite by default, MySQL by setting DATABASE_URL.

    SQLite (default):  nothing to configure, creates ecommerce.db
    MySQL:             export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/ecommerce"
                       (create the empty database first:  CREATE DATABASE ecommerce;)
"""
import os
from sqlalchemy import (Column, Date, Float, ForeignKey, Integer, MetaData, String, Table, create_engine)

from config import ROOT


def get_engine():
    url = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'ecommerce.db'}")
    return create_engine(url)


metadata = MetaData()

customers = Table(
    "customers", metadata,
    Column("customer_id", Integer, primary_key=True, autoincrement=False),
    Column("name", String(100), nullable=False),
    Column("email", String(150)),
    Column("location", String(60)),
    Column("region", String(20)),
    Column("registration_date", Date, nullable=False),
)

products = Table(
    "products", metadata,
    Column("product_id", Integer, primary_key=True, autoincrement=False),
    Column("product_name", String(100), nullable=False),
    Column("category", String(60), nullable=False),
    Column("price", Float, nullable=False),
    Column("cost_price", Float, nullable=False),
    Column("stock_quantity", Integer),
)

orders = Table(
    "orders", metadata,
    Column("order_id", Integer, primary_key=True, autoincrement=False),
    Column("customer_id", Integer, ForeignKey("customers.customer_id"), nullable=False, index=True),
    Column("order_date", Date, nullable=False, index=True),
    Column("order_status", String(20), nullable=False),
    Column("payment_method", String(30)),
    Column("total_amount", Float),
)

order_items = Table(
    "order_items", metadata,
    Column("item_id", Integer, primary_key=True, autoincrement=False),
    Column("order_id", Integer, ForeignKey("orders.order_id"), nullable=False, index=True),
    Column("product_id", Integer, ForeignKey("products.product_id"), nullable=False, index=True),
    Column("quantity", Integer, nullable=False),
    Column("unit_price", Float, nullable=False),
    Column("discount_pct", Integer, nullable=False),
)

LOAD_ORDER = ["customers", "products", "orders", "order_items"]
DATE_COLUMNS = {"customers": ["registration_date"], "orders": ["order_date"]}
