-- Example analysis queries (standard SQL, run on both MySQL and SQLite).
-- "Valid" sales exclude Cancelled and Returned orders.

-- 1. Headline KPIs
SELECT ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100.0)), 2)                     AS revenue,
       ROUND(SUM(oi.quantity * (oi.unit_price * (1 - oi.discount_pct / 100.0) - p.cost_price)), 2)    AS profit,
       COUNT(DISTINCT o.order_id)                                                                      AS orders,
       COUNT(DISTINCT o.customer_id)                                                                   AS customers
FROM order_items oi
JOIN orders   o ON o.order_id   = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.order_status IN ('Delivered', 'Shipped', 'Processing');

-- 2. Monthly revenue trend
SELECT SUBSTR(o.order_date, 1, 7) AS month,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100.0)), 2) AS revenue,
       COUNT(DISTINCT o.order_id) AS orders
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('Delivered', 'Shipped', 'Processing')
GROUP BY SUBSTR(o.order_date, 1, 7)
ORDER BY month;

-- 3. Category performance
SELECT p.category,
       SUM(oi.quantity) AS units,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100.0)), 2) AS revenue,
       ROUND(SUM(oi.quantity * (oi.unit_price * (1 - oi.discount_pct / 100.0) - p.cost_price))
             / SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100.0)) * 100, 1) AS margin_pct
FROM order_items oi
JOIN orders   o ON o.order_id   = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.order_status IN ('Delivered', 'Shipped', 'Processing')
GROUP BY p.category
ORDER BY revenue DESC;

-- 4. Top 10 customers by revenue
SELECT c.customer_id, c.name, c.location,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100.0)), 2) AS revenue
FROM customers c
JOIN orders      o  ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id   = o.order_id
WHERE o.order_status IN ('Delivered', 'Shipped', 'Processing')
GROUP BY c.customer_id, c.name, c.location
ORDER BY revenue DESC
LIMIT 10;

-- 5. Products that never sold (low performers)
SELECT p.product_id, p.product_name, p.category, p.stock_quantity
FROM products p
WHERE p.product_id NOT IN (
    SELECT oi.product_id
    FROM order_items oi JOIN orders o ON o.order_id = oi.order_id
    WHERE o.order_status IN ('Delivered', 'Shipped', 'Processing'));
