CREATE TABLE positions (
    position_id SERIAL PRIMARY KEY,
    position_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    position_id INT NOT NULL REFERENCES positions(position_id),
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(50) NOT NULL,
    hire_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE restaurant_tables(
    table_id SERIAL PRIMARY KEY,
    seats INT NOT NULL,
    place VARCHAR(50) NOT NULL CHECK (place IN ('Hall', 'Terrace')),
    is_active BOOLEAN NOT NULL
);

CREATE TABLE menu_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE menu_items (
    menu_item_id SERIAL PRIMARY KEY,
    menu_item_name VARCHAR(50) NOT NULL UNIQUE,
    category_id INT NOT NULL REFERENCES menu_categories(category_id),
    menu_item_description VARCHAR(200) NOT NULL,
    price NUMERIC(10,2) NOT NULL
);


CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    employee_id INT NOT NULL REFERENCES employees(employee_id),
    table_id INT NOT NULL REFERENCES restaurant_tables(table_id),
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    order_status VARCHAR(20) NOT NULL CHECK (order_status IN ('NEW', 'PREPARING', 'READY', 'PAID', 'CANCELLED'))
);
   
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id),
    menu_item_id INT NOT NULL REFERENCES menu_items(menu_item_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10,2) NOT NULL
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_employee_id ON orders(employee_id);
CREATE INDEX idx_orders_table_id ON orders(table_id);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_orders_time ON orders(order_time);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_menu_item_id ON order_items(menu_item_id);
CREATE INDEX idx_menu_items_category ON menu_items(category_id);
