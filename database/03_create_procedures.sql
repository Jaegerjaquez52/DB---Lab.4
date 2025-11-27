-- Процедура 1: Створення замовлення з автоматичним додаванням позицій
-- Використання: 
-- Створити замовлення для клієнта 1, обслуговує офіціант 2, стіл 3
-- Замовити страви: ID 1 (2 шт), ID 5 (1 шт), ID 9 (1 шт)
-- SELECT * FROM create_order_with_items(
--     1,                  | customer_id
--     2,                  | employee_id
--     3,                  | table_id
--     ARRAY[1, 5, 9],     | menu_item_ids
--     ARRAY[2, 1, 1]      | quantities
-- );

CREATE OR REPLACE FUNCTION create_order_with_items(
    p_customer_id INT,
    p_employee_id INT,
    p_table_id INT,
    p_menu_item_ids INT[],
    p_quantities INT[]
) RETURNS TABLE(
    order_id INT,
    total_amount DECIMAL,
    items_count INT
) AS $$
DECLARE
    v_order_id INT;
    v_total DECIMAL := 0;
    v_item_id INT;
    v_quantity INT;
    v_price DECIMAL;
    i INT;
BEGIN
    -- Перевірка, що масиви однакової довжини
    IF array_length(p_menu_item_ids, 1) != array_length(p_quantities, 1) THEN
        RAISE EXCEPTION 'Кількість страв та кількостей не співпадає';
    END IF;

    -- Створення замовлення
    INSERT INTO orders (customer_id, employee_id, table_id, order_status)
    VALUES (p_customer_id, p_employee_id, p_table_id, 'NEW')
    RETURNING orders.order_id INTO v_order_id;

    -- Додавання позицій замовлення
    FOR i IN 1..array_length(p_menu_item_ids, 1) LOOP
        v_item_id := p_menu_item_ids[i];
        v_quantity := p_quantities[i];
        
        -- Отримання ціни страви
        SELECT price INTO v_price
        FROM menu_items
        WHERE menu_item_id = v_item_id;
        
        IF v_price IS NULL THEN
            RAISE EXCEPTION 'Страва з ID % не знайдена', v_item_id;
        END IF;
        
        -- Додавання позиції
        INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price)
        VALUES (v_order_id, v_item_id, v_quantity, v_price);
        
        v_total := v_total + (v_quantity * v_price);
    END LOOP;

    -- Повернення результату
    RETURN QUERY
    SELECT v_order_id, v_total, array_length(p_menu_item_ids, 1);
END;
$$ LANGUAGE plpgsql;


-- Процедура 2: Оновлення статусу замовлення з перевіркою
-- Використання: 
    --Змінити статус замовлення #1 на "PAID"
    --SELECT * FROM update_order_status(1, 'PAID');

CREATE OR REPLACE FUNCTION update_order_status(
    p_order_id INT,
    p_new_status VARCHAR
) RETURNS TABLE(
    order_id INT,
    old_status VARCHAR,
    new_status VARCHAR,
    updated_at TIMESTAMP
) AS $$
DECLARE
    v_old_status VARCHAR;
    v_current_time TIMESTAMP := CURRENT_TIMESTAMP;
BEGIN
    -- Перевірка чи існує замовлення
    SELECT order_status INTO v_old_status
    FROM orders
    WHERE orders.order_id = p_order_id;
    
    IF v_old_status IS NULL THEN
        RAISE EXCEPTION 'Замовлення з ID % не знайдено', p_order_id;
    END IF;
    
    -- Перевірка валідності нового статусу
    IF p_new_status NOT IN ('NEW', 'PREPARING', 'READY', 'PAID', 'CANCELLED') THEN
        RAISE EXCEPTION 'Невірний статус: %', p_new_status;
    END IF;
    
    -- Перевірка логічності переходу статусу
    IF v_old_status = 'PAID' AND p_new_status != 'CANCELLED' THEN
        RAISE EXCEPTION 'Неможливо змінити статус оплаченого замовлення';
    END IF;
    
    IF v_old_status = 'CANCELLED' THEN
        RAISE EXCEPTION 'Неможливо змінити статус скасованого замовлення';
    END IF;
    
    -- Оновлення статусу
    UPDATE orders
    SET order_status = p_new_status
    WHERE orders.order_id = p_order_id;
    
    -- Повернення результату
    RETURN QUERY
    SELECT p_order_id, v_old_status, p_new_status, v_current_time;
END;
$$ LANGUAGE plpgsql;


-- Процедура 3: Розрахунок загальної виручки за період

CREATE OR REPLACE FUNCTION calculate_revenue(
    p_start_date TIMESTAMPTZ,
    p_end_date TIMESTAMPTZ
) RETURNS TABLE(
    total_orders INT,
    total_revenue DECIMAL,
    avg_order_value DECIMAL,
    paid_orders INT,
    cancelled_orders INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT o.order_id)::INT AS total_orders,
        COALESCE(SUM(oi.quantity * oi.unit_price), 0)::DECIMAL(10,2) AS total_revenue,
        COALESCE(AVG(order_totals.order_total), 0)::DECIMAL(10,2) AS avg_order_value,
        COUNT(DISTINCT CASE WHEN o.order_status = 'PAID' THEN o.order_id END)::INT AS paid_orders,
        COUNT(DISTINCT CASE WHEN o.order_status = 'CANCELLED' THEN o.order_id END)::INT AS cancelled_orders
    FROM orders o
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN (
        SELECT order_id, SUM(quantity * unit_price) AS order_total
        FROM order_items
        GROUP BY order_id
    ) AS order_totals ON o.order_id = order_totals.order_id
    WHERE o.order_time BETWEEN p_start_date AND p_end_date;
END;
$$ LANGUAGE plpgsql;