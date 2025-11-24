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
    e.position AS employee_position,
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
INNER JOIN restaurant_tables rt ON o.table_id = rt.table_id;


-- Показує продуктивність кожного працівника
CREATE OR REPLACE VIEW view_employee_statistics AS
SELECT 
    e.employee_id,
    e.first_name || ' ' || e.last_name AS employee_name,
    e.position,
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
LEFT JOIN orders o ON e.employee_id = o.employee_id AND o.order_status != 'CANCELLED'
GROUP BY e.employee_id, e.first_name, e.last_name, e.position, e.phone, e.email;
    


-- Показує найчастіше замовлювані страви
CREATE OR REPLACE VIEW view_popular_dishes AS
SELECT 
    mi.menu_item_id,
    mi.menu_item_name,
    mi.category,
    mi.price,
    COUNT(DISTINCT oi.order_id) AS times_ordered,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.quantity * oi.unit_price) AS total_revenue,
    AVG(oi.quantity) AS avg_quantity_per_order
FROM menu_items mi
INNER JOIN order_items oi ON mi.menu_item_id = oi.menu_item_id
INNER JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status != 'CANCELLED'
GROUP BY mi.menu_item_id, mi.menu_item_name, mi.category, mi.price
ORDER BY times_ordered DESC, total_revenue DESC;
