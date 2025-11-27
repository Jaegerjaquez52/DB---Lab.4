-- Додавання клієнтів
INSERT INTO customers (first_name, last_name, phone, email) VALUES
('Олександр', 'Коваленко', '+380501234567', 'kovalenko@gmail.com'),
('Марія', 'Шевченко', '+380502345678', 'shevchenko@gmail.com'),
('Іван', 'Мельник', '+380503456789', 'melnyk@gmail.com'),
('Олена', 'Бондаренко', '+380504567890', 'bondarenko@gmail.com'),
('Петро', 'Ткаченко', '+380505678901', 'tkachenko@gmail.com'),
('Тетяна', 'Кравченко', '+380506789012', 'kravchenko@gmail.com'),
('Андрій', 'Морозов', '+380507890123', 'morozov@gmail.com'),
('Наталія', 'Павленко', '+380508901234', 'pavlenko@gmail.com'),
('Сергій', 'Савченко', '+380509012345', 'savchenko@gmail.com'),
('Юлія', 'Литвин', '+380500123456', 'lytvyn@gmail.com');

-- Додавання посад
INSERT INTO positions (position_name) VALUES 
('Офіціант'), 
('Кухар'), 
('Адміністратор'),
('Бармен') ;

-- Додавання працівників
INSERT INTO employees (first_name, last_name, position_id, phone, email) VALUES
('Дмитро', 'Іваненко', '1', '+380671234567', 'ivanenko@gmail.com'),
('Вікторія', 'Романенко', '1', '+380672345678', 'romanenko@gmail.com'),
('Максим', 'Гончаренко', '2', '+380673456789', 'honcharenko@gmail.com'),
('Оксана', 'Валисенко', '3', '+380674567890', 'vasylenko@gmail.com'),
('Володимир', 'Петренко', '1', '+380675678901', 'petrenko@gmail.com'),
('Катерина', 'Семенова', '4', '+380676789012', 'semenova@gmail.com'),
('Роман', 'Білоус', '2', '+380677890123', 'bilous@gmail.com'),
('Аліна', 'Кузьменко', '1', '+380678901234', 'kuzmenko@gmail.com'),
('Богдан', 'Захарченко', '2', '+380679012345', 'zakharchenko@gmail.com'),
('Ірина', 'Мороз', '3', '+380670123456', 'moroz@gmail.com');

-- Додавання паролів для адміністраторів
UPDATE employees
SET password_hash = 'pbkdf2:sha256:1000000$09lILaEgQmlRoXFn$db913fcc676137f5c90c47d7f7ed3efa9af9e95dcdd55073ff11d6e890865edc'
WHERE position_id = (SELECT position_id FROM positions WHERE position_name = 'Адміністратор');

-- Додавання паролів для решти працівників
UPDATE employees
SET password_hash = 'pbkdf2:sha256:1000000$09lILaEgQmlRoXFn$db913fcc676137f5c90c47d7f7ed3efa9af9e95dcdd55073ff11d6e890865edc'
WHERE password_hash IS NULL;

-- Додавання столів
INSERT INTO restaurant_tables (seats, place, is_active) VALUES
(2, 'Hall', TRUE),
(4, 'Hall', TRUE),
(4, 'Hall', TRUE),
(6, 'Hall', TRUE),
(2, 'Terrace', TRUE),
(4, 'Terrace', TRUE),
(4, 'Terrace', TRUE),
(6, 'Terrace', TRUE),
(8, 'Hall', TRUE),
(2, 'Hall', FALSE);

INSERT INTO menu_categories (category_name)
    VALUES
    ('Супи'), 
    ('Салати'),
    ('Гарячі страви'), 
    ('Паста'), 
    ('Десерти'), 
    ('Напої'), 
    ('Алкоголь');

-- Додавання страв у меню
INSERT INTO menu_items (category_id, menu_item_name, menu_item_description, price) VALUES
-- Супи
((SELECT category_id FROM menu_categories WHERE category_name='Супи'), 'Борщ український', 'Традиційний український борщ зі сметаною', 85.00), 
((SELECT category_id FROM menu_categories WHERE category_name='Супи'), 'Солянка м''ясна', 'Густий суп з різними видами м''яса', 95.00),
((SELECT category_id FROM menu_categories WHERE category_name='Супи'), 'Грибний крем-суп', 'Ніжний суп з печериць та вершків з грінками', 90.00),
((SELECT category_id FROM menu_categories WHERE category_name='Супи'), 'Курячий бульйон', 'Легкий бульйон з перепелиним яйцем та локшиною', 75.00),
-- Салати
((SELECT category_id FROM menu_categories WHERE category_name='Салати'), 'Салат Цезар', 'Класичний салат з куркою та соусом Цезар', 120.00),
((SELECT category_id FROM menu_categories WHERE category_name='Салати'), 'Грецький салат', 'Свіжі овочі з сиром фета та оливками', 105.00),
((SELECT category_id FROM menu_categories WHERE category_name='Салати'), 'Теплий салат з телятиною', 'Мікс салату, телятина гриль, гірчичний соус', 145.00),
((SELECT category_id FROM menu_categories WHERE category_name='Салати'), 'Салат з тунцем', 'Консервований тунець, яйце, свіжі овочі', 130.00),
-- Гарячі
((SELECT category_id FROM menu_categories WHERE category_name='Гарячі страви'), 'Стейк Рібай', 'Соковитий стейк з яловичини 300г', 450.00),
((SELECT category_id FROM menu_categories WHERE category_name='Гарячі страви'), 'Курка по-київськи', 'Фірмова страва ресторану з картопляним пюре', 280.00),
((SELECT category_id FROM menu_categories WHERE category_name='Гарячі страви'), 'Стейк з лосося', 'Стейк з лосося на грилі з лимонним соусом', 380.00),
((SELECT category_id FROM menu_categories WHERE category_name='Гарячі страви'), 'Бургер Яловичий', 'Булочка бріош, котлета з яловичини, сир чеддер', 220.00), 
((SELECT category_id FROM menu_categories WHERE category_name='Гарячі страви'), 'Качина грудка', 'Філе качки з ягідним соусом', 320.00),
((SELECT category_id FROM menu_categories WHERE category_name='Гарячі страви'), 'Овочі гриль', 'Баклажан, цукіні, перець, печериці', 110.00),
-- Паста
((SELECT category_id FROM menu_categories WHERE category_name='Паста'), 'Паста Карбонара', 'Італійська паста з беконом та вершковим соусом', 185.00), 
((SELECT category_id FROM menu_categories WHERE category_name='Паста'), 'Лазанья Болоньєзе', 'Класична італійська лазанья з м''ясним соусом', 195.00),
((SELECT category_id FROM menu_categories WHERE category_name='Паста'), 'Паста з морепродуктами', 'Спагеті з креветками, мідіями та кальмарами', 240.00),
((SELECT category_id FROM menu_categories WHERE category_name='Паста'), 'Різотто з грибами', 'Італійський рис арборіо з білими грибами', 190.00),
-- Десерти
((SELECT category_id FROM menu_categories WHERE category_name='Десерти'), 'Тірамісу', 'Італійський десерт з маскарпоне', 95.00),
((SELECT category_id FROM menu_categories WHERE category_name='Десерти'), 'Чізкейк Нью-Йорк', 'Класичний американський чізкейк', 105.00),
((SELECT category_id FROM menu_categories WHERE category_name='Десерти'), 'Шоколадний фондан', 'Кекс з рідкою шоколадною начинкою та морозивом', 115.00),
((SELECT category_id FROM menu_categories WHERE category_name='Десерти'), 'Наполеон', 'Класичний торт з заварним кремом', 90.00),
((SELECT category_id FROM menu_categories WHERE category_name='Десерти'), 'Морозиво асорті', 'Три кульки морозива на вибір', 60.00),
-- Напої
((SELECT category_id FROM menu_categories WHERE category_name='Напої'), 'Кава Еспресо', 'Міцна італійська кава', 45.00),
((SELECT category_id FROM menu_categories WHERE category_name='Напої'), 'Капучино', 'Кава з молочною пінкою', 55.00),
((SELECT category_id FROM menu_categories WHERE category_name='Напої'), 'Лимонад домашній', 'Освіжаючий лимонад власного приготування', 65.00),
((SELECT category_id FROM menu_categories WHERE category_name='Напої'), 'Чай заварний', 'Чорний, зелений або трав''яний (чайник)', 55.00),
((SELECT category_id FROM menu_categories WHERE category_name='Напої'), 'Фреш апельсиновий', 'Свіжовижатий сік 200мл', 80.00),
((SELECT category_id FROM menu_categories WHERE category_name='Напої'), 'Вода Моршинська', 'Мінеральна вода (скло) 0.5л', 40.00),
-- Алкоголь
((SELECT category_id FROM menu_categories WHERE category_name='Алкоголь'), 'Вино червоне', 'Червоне сухе вино, 150мл', 120.00),
((SELECT category_id FROM menu_categories WHERE category_name='Алкоголь'), 'Вино біле', 'Біле напівсухе вино, 150мл', 110.00),
((SELECT category_id FROM menu_categories WHERE category_name='Алкоголь'), 'Пиво розливне', 'Світле нефільтроване, 0.5л', 70.00),
((SELECT category_id FROM menu_categories WHERE category_name='Алкоголь'), 'Коктейль Мохіто', 'Ром, м''ята, лайм, содова', 140.00);

-- Додавання замовлень
INSERT INTO orders (order_id, customer_id, employee_id, table_id, order_time, order_status) VALUES
(1, 1, 1, 1, NOW() - INTERVAL '2 days', 'PAID'),
(2, 2, 2, 3, NOW() - INTERVAL '1 day', 'PAID'),
(3, 3, 1, 5, NOW() - INTERVAL '5 hours', 'READY'),
(4, 4, 5, 2, NOW() - INTERVAL '3 hours', 'PREPARING'),
(5, 5, 8, 4, NOW() - INTERVAL '30 minutes', 'NEW'),
(6, 6, 2, 6, NOW() - INTERVAL '1 day', 'PAID'),
(7, 7, 1, 7, NOW() - INTERVAL '4 hours', 'PAID'),
(8, 8, 5, 8, NOW() - INTERVAL '1 hour', 'PREPARING'),
(9, 9, 8, 1, NOW() - INTERVAL '10 minutes', 'NEW'),
(10, 10, 2, 3, NOW() - INTERVAL '6 hours', 'PAID');

-- Скидання лічильника ID
SELECT setval('orders_order_id_seq', (SELECT MAX(order_id) FROM orders));

-- Додавання позицій замовлень
INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price) VALUES
-- Замовлення 1
(1, 1, 1, 85.00),
(1, 12, 1, 220.00),
(1, 25, 2, 55.00),

-- Замовлення 2
(2, 5, 2, 120.00),
(2, 18, 2, 190.00),
(2, 31, 2, 110.00),

-- Замовлення 3
(3, 3, 1, 90.00),
(3, 12, 1, 220.00),
(3, 21, 1, 115.00),

-- Замовлення 4
(4, 12, 1, 220.00),
(4, 25, 2, 55.00),

-- Замовлення 5
(5, 5, 2, 120.00),
(5, 9, 2, 450.00),
(5, 25, 1, 55.00),
(5, 30, 2, 120.00),

-- Замовлення 6
(6, 15, 1, 185.00),
(6, 1, 1, 85.00),

-- Замовлення 7
(7, 10, 2, 280.00),
(7, 5, 1, 120.00),
(7, 25, 2, 55.00),

-- Замовлення 8
(8, 7, 1, 145.00),
(8, 1, 1, 85.00),
(8, 26, 1, 65.00),

-- Замовлення 9
(9, 12, 2, 220.00),
(9, 15, 2, 185.00),
(9, 29, 2, 40.00),

-- Замовлення 10
(10, 19, 1, 95.00),
(10, 25, 1, 55.00);