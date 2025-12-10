-- Таблиця для аудиту для замовлень
CREATE TABLE IF NOT EXISTS order_audit (
    audit_id SERIAL PRIMARY KEY,
    order_id INT,
    action VARCHAR(10),
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    changed_by VARCHAR(50),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ТРИГЕР 1: Логування змін статусу замовлення
CREATE OR REPLACE FUNCTION log_order_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- 1. Якщо створюється нове замовлення
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO order_audit (order_id, action, old_status, new_status, changed_by)
        VALUES (NEW.order_id, 'CREATE', NULL, NEW.order_status, current_user);
        RETURN NEW;

    -- 2. Якщо замовлення оновлюється
    ELSIF (TG_OP = 'UPDATE') THEN
        -- Використовуємо IS DISTINCT FROM, щоб коректно обробляти NULL значення
        IF OLD.order_status IS DISTINCT FROM NEW.order_status THEN
            INSERT INTO order_audit (order_id, action, old_status, new_status, changed_by)
            VALUES (NEW.order_id, 'UPDATE', OLD.order_status, NEW.order_status, current_user);
        END IF;
        RETURN NEW;

    -- 3. Якщо замовлення видаляється
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO order_audit (order_id, action, old_status, changed_by)
        VALUES (OLD.order_id, 'DELETE', OLD.order_status, current_user);
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_order_status_change
AFTER INSERT OR UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION log_order_status_change();


-- ТРИГЕР 2: Логування змін цін у меню
CREATE OR REPLACE FUNCTION log_price_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Логувати тільки якщо ціна змінилася
    IF OLD.price != NEW.price THEN
        INSERT INTO price_history (menu_item_id, old_price, new_price, changed_by)
        VALUES (NEW.menu_item_id, OLD.price, NEW.price, current_user);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_price_change
AFTER UPDATE ON menu_items
FOR EACH ROW
EXECUTE FUNCTION log_price_change();


-- ТРИГЕР 3: Автоматична валідація замовлення перед вставкою
CREATE OR REPLACE FUNCTION validate_order_before_insert()
RETURNS TRIGGER AS $$
BEGIN
    -- Перевірка 1: Клієнт існує
    IF NOT EXISTS (SELECT 1 FROM customers WHERE customer_id = NEW.customer_id) THEN
        RAISE EXCEPTION 'Клієнта з ID % не існує', NEW.customer_id;
    END IF;
    
    -- Перевірка 2: Працівник існує
    IF NOT EXISTS (SELECT 1 FROM employees WHERE employee_id = NEW.employee_id) THEN
        RAISE EXCEPTION 'Працівника з ID % не існує', NEW.employee_id;
    END IF;
    
    -- Перевірка 3: Стіл існує та активний
    IF NOT EXISTS (SELECT 1 FROM restaurant_tables 
                   WHERE table_id = NEW.table_id AND is_active = TRUE) THEN
        RAISE EXCEPTION 'Стіл з ID % не існує або неактивний', NEW.table_id;
    END IF;
    
    -- Перевірка 4: Статус валідний
    IF NEW.order_status NOT IN ('NEW', 'PREPARING', 'READY', 'PAID', 'CANCELLED') THEN
        RAISE EXCEPTION 'Невірний статус замовлення: %', NEW.order_status;
    END IF;

    IF EXISTS (
    SELECT 1 FROM orders 
    WHERE table_id = NEW.table_id 
    AND order_status IN ('NEW', 'PREPARING', 'READY')
    -- Важливо: якщо це UPDATE, не блокувати саме себе
    AND (TG_OP = 'INSERT' OR order_id != NEW.order_id) )
    THEN
        RAISE EXCEPTION 'Стіл % вже зайнятий активним замовленням', NEW.table_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_order
BEFORE INSERT ON orders
FOR EACH ROW
EXECUTE FUNCTION validate_order_before_insert();

-- ТРИГЕР 4: Оновлення кешу, коли замовлення оплачується або змінюється
CREATE OR REPLACE FUNCTION refresh_revenue_cache()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_daily_revenue_cache;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_refresh_revenue_cache
AFTER UPDATE OF order_status OR INSERT ON orders
FOR EACH ROW
WHEN (NEW.order_status = 'PAID')
EXECUTE FUNCTION refresh_revenue_cache();
