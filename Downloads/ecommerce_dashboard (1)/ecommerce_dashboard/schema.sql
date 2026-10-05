-- MySQL schema (reference copy of database.py). Run in MySQL Workbench if you prefer SQL over Python.
CREATE DATABASE IF NOT EXISTS ecommerce;
USE ecommerce;

CREATE TABLE customers (
    customer_id       INT PRIMARY KEY,
    name              VARCHAR(100) NOT NULL,
    email             VARCHAR(150),
    location          VARCHAR(60),
    region            VARCHAR(20),
    registration_date DATE NOT NULL
);

CREATE TABLE products (
    product_id     INT PRIMARY KEY,
    product_name   VARCHAR(100) NOT NULL,
    category       VARCHAR(60)  NOT NULL,
    price          DOUBLE NOT NULL,
    cost_price     DOUBLE NOT NULL,
    stock_quantity INT
);

CREATE TABLE orders (
    order_id       INT PRIMARY KEY,
    customer_id    INT NOT NULL,
    order_date     DATE NOT NULL,
    order_status   VARCHAR(20) NOT NULL,
    payment_method VARCHAR(30),
    total_amount   DOUBLE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    INDEX idx_orders_customer (customer_id),
    INDEX idx_orders_date (order_date)
);

CREATE TABLE order_items (
    item_id      INT PRIMARY KEY,
    order_id     INT NOT NULL,
    product_id   INT NOT NULL,
    quantity     INT NOT NULL,
    unit_price   DOUBLE NOT NULL,
    discount_pct INT NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_items_order (order_id),
    INDEX idx_items_product (product_id)
);
