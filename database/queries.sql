-- Отримати всі активні столи, відсортовані за кількістю місць
SELECT table_id, seats, place, is_active
FROM restaurant_tables
WHERE is_active = TRUE
ORDER BY seats DESC, place;

-- Показати всі замовлення з іменами клієнтів
SELECT 
    o.order_id,
    o.order_time,
    o.order_status,
    c.first_name,
    c.last_name,
    c.phone
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
ORDER BY o.order_time DESC;

-- Показати замовлення з клієнтами, офіціантами та столами
SELECT 
    o.order_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    e.first_name || ' ' || e.last_name AS employee_name,
    e.position,
    rt.table_id,
    rt.place,
    o.order_time,
    o.order_status
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN employees e ON o.employee_id = e.employee_id
INNER JOIN restaurant_tables rt ON o.table_id = rt.table_id
ORDER BY o.order_time DESC;

-- Підрахувати кількість замовлень кожного клієнта
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email,
    COUNT(o.order_id) AS total_orders
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
ORDER BY total_orders DESC;

-- Статистика по категоріях меню
SELECT 
    category,
    COUNT(*) AS items_count,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price
FROM menu_items
GROUP BY category
ORDER BY avg_price DESC;

-- Загальна сума кожного замовлення
SELECT 
    o.order_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    o.order_time,
    o.order_status,
    SUM(oi.quantity * oi.unit_price) AS total_amount
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, c.first_name, c.last_name, o.order_time, o.order_status
ORDER BY total_amount DESC;

-- ========================
-- Робота з представленнями
-- ========================

-- Замовлення конкретного клієнта
SELECT * FROM view_orders_full WHERE customer_id = 1;

-- Топ працівників за виручкою
SELECT * FROM view_employee_statistics ORDER BY total_revenue DESC;

-- Топ-10 найпопулярніших страв
SELECT * FROM view_popular_dishes LIMIT 10;

-- Популярні десерти
SELECT * FROM view_popular_dishes WHERE category = 'Десерти';