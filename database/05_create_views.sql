-- Об'єднує дані про замовлення, клієнтів, офіціантів та столи
CREATE OR REPLACE VIEW view_orders_full AS
SELECT 
    o.order_id,
    o.order_time,
    o.order_status,
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.phone AS customer_phone,
    c.email AS customer_email,
    e.employee_id,
    e.first_name || ' ' || e.last_name AS employee_name,
    p.position_name AS employee_position,
    rt.table_id,
    rt.seats,
    rt.place AS table_location,
    COALESCE(
        (SELECT SUM(oi.quantity * oi.unit_price) 
         FROM order_items oi 
         WHERE oi.order_id = o.order_id), 
        0
    ) AS total_amount
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN employees e ON o.employee_id = e.employee_id
INNER JOIN positions p ON e.position_id = p.position_id 
INNER JOIN restaurant_tables rt ON o.table_id = rt.table_id;


-- Показує продуктивність кожного працівника (ТІЛЬКИ ОФІЦІАНТИ)
CREATE OR REPLACE VIEW view_employee_statistics AS
SELECT 
    e.employee_id,
    e.first_name || ' ' || e.last_name AS employee_name,
    p.position_name AS position,
    e.phone,
    e.email,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COALESCE(SUM(
        (SELECT SUM(oi.quantity * oi.unit_price) 
         FROM order_items oi 
         WHERE oi.order_id = o.order_id)
    ), 0) AS total_revenue,
    COALESCE(AVG(
        (SELECT SUM(oi.quantity * oi.unit_price) 
         FROM order_items oi 
         WHERE oi.order_id = o.order_id)
    ), 0) AS avg_order_value,
    MIN(o.order_time) AS first_order_date,
    MAX(o.order_time) AS last_order_date
FROM employees e
INNER JOIN positions p ON e.position_id = p.position_id
LEFT JOIN orders o ON e.employee_id = o.employee_id AND o.order_status != 'CANCELLED'
WHERE p.position_name = 'Офіціант' 
GROUP BY e.employee_id, e.first_name, e.last_name, p.position_name, e.phone, e.email;


-- Показує найчастіше замовлювані страви
CREATE OR REPLACE VIEW view_popular_dishes AS
SELECT 
    mi.menu_item_id,
    mi.menu_item_name,
    mc.category_name AS category, -- ЗМІНА: беремо з нової таблиці
    COUNT(oi.order_item_id) AS times_ordered,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_revenue
FROM menu_items mi
INNER JOIN menu_categories mc ON mi.category_id = mc.category_id -- НОВЕ ПРИЄДНАННЯ
INNER JOIN order_items oi ON mi.menu_item_id = oi.menu_item_id
INNER JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status != 'CANCELLED'
GROUP BY mi.menu_item_id, mi.menu_item_name, mc.category_name
ORDER BY times_ordered DESC, total_revenue DESC
LIMIT 10;