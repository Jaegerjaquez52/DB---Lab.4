-- 1. Створення ролі для веб-додатку
CREATE ROLE flask_app_role;

-- 2. Базові права на підключення
GRANT CONNECT ON DATABASE restaurant TO flask_app_role;
GRANT USAGE ON SCHEMA public TO flask_app_role;

-- =========================================================
-- НАЛАШТУВАННЯ ОБМЕЖЕНИХ ПРАВ (Limited Access)
-- =========================================================

-- 3. ТАБЛИЦІ ТІЛЬКИ ДЛЯ ЧИТАННЯ (Reference Data)
GRANT SELECT ON positions, menu_categories, restaurant_tables TO flask_app_role;

-- 4. ТАБЛИЦІ ДЛЯ ЧИТАННЯ ТА ЗАПИСУ 
GRANT SELECT, INSERT, UPDATE, DELETE ON 
    customers, 
    employees, 
    menu_items, 
    orders, 
    order_items 
TO flask_app_role;

-- 5. ПРАВА ДЛЯ ТРИГЕРІВ (Аудит)
GRANT INSERT, SELECT ON order_audit TO flask_app_role;

-- 6. ПРАВА НА ПРЕДСТАВЛЕННЯ (Views)
GRANT SELECT ON 
    view_orders_full, 
    view_employee_statistics, 
    view_popular_dishes,
    view_stats_last_30_days
TO flask_app_role;

-- 7. ПРАВА НА ПОСЛІДОВНОСТІ (Sequences) 
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO flask_app_role;

-- 8. ПРАВА НА ФУНКЦІЇ
GRANT EXECUTE ON FUNCTION update_order_status(INT, VARCHAR) TO flask_app_role;
GRANT EXECUTE ON FUNCTION create_order_with_items(INT, INT, INT, INT[], INT[]) TO flask_app_role;
GRANT EXECUTE ON FUNCTION calculate_revenue(TIMESTAMPTZ, TIMESTAMPTZ) TO flask_app_role;

-- =========================================================
-- СТВОРЕННЯ КОРИСТУВАЧА
-- =========================================================

-- Створюємо конкретного юзера, якого пропишемо в app.py
-- ЗАМІНІТЬ 'secure_pass_2025' НА СВІЙ ПАРОЛЬ
CREATE USER app_user WITH PASSWORD 'password';

-- Призначаємо йому налаштовану роль
GRANT flask_app_role TO app_user;
