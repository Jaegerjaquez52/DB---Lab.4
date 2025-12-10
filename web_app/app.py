from flask import Flask, Response, render_template, request, redirect, url_for, flash, session, g 
from database import DatabaseConnection
from io import StringIO
import re
import csv
from werkzeug.security import generate_password_hash, check_password_hash 
from functools import wraps 

# Ініціалізація Flask додатку
app = Flask(__name__)
app.secret_key = '12345'



# Підключення до бази даних
db = DatabaseConnection(
    dbname='restaurant',
    user='app_user',           
    password='password', 
    host='postgres',
    port=5432
)
db.connect()

# ============================================================
# АУТЕНТИФІКАЦІЯ
# ============================================================

# Декоратор, який перевіряє, чи користувач увійшов
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employee_id' not in session: # Перевіряємо за наявністю ID в сесії
            flash('Ця сторінка вимагає авторизації.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Спочатку перевіряємо, чи користувач взагалі увійшов
            if 'employee_id' not in session:
                return redirect(url_for('login'))
            
            # Перевіряємо роль
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash('У вас недостатньо прав для цієї дії.', 'error')
                return redirect(request.referrer or url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.before_request
def load_logged_in_user():
    """Завантажує дані працівника перед кожним запитом, якщо він увійшов."""
    user = get_current_employee()
    g.employee = user # Зберігаємо в об'єкті g
    # g.employee буде None, якщо користувач не увійшов
    
# Допоміжна функція для отримання поточного працівника з БД
def get_current_employee():
    employee_id = session.get('employee_id')
    if employee_id:
        try:
            employee = db.execute_one(
                "SELECT employee_id, first_name, last_name, email, position_id FROM employees WHERE employee_id = %s", 
                (employee_id,)
            )
            return employee
        except Exception as e:
            print(f"Помилка при отриманні даних працівника: {e}")
            return None
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    title = "Вхід до системи"
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        try:
            query = """
                SELECT e.employee_id, e.first_name, e.last_name, e.password_hash, p.position_name 
                FROM employees e
                JOIN positions p ON e.position_id = p.position_id
                WHERE e.email = %s
            """
            results = db.execute_query(query, (email,))
            
            user = results[0] if results else None
            
            if user:
                stored_hash = user.get('password_hash')
                
                if stored_hash and check_password_hash(stored_hash, password):
                    session['employee_id'] = user['employee_id']
                    session['employee_name'] = f"{user['first_name']} {user['last_name']}"
                    
                    session['role'] = user['position_name'] 
                    
                    flash(f'Вітаємо, {user["first_name"]} ({user["position_name"]})!', 'success')
                    return redirect(url_for('index'))
                
            flash('Невірний email або пароль.', 'danger')
            
        except Exception as e:
            print(f"Помилка входу: {e}")
            flash('Помилка сервера.', 'danger')
            
    return render_template('login.html', title=title)

@app.route('/logout')
def logout():
    session.pop('employee_id', None)
    session.pop('employee_name', None)
    flash('Ви успішно вийшли.', 'info')
    return redirect(url_for('login'))

# ============================================================
# Валідація
# ============================================================
def validate_name(name):
    """Перевіряє, чи ім'я містить лише літери (кирилиця/латиниця), пробіли, апострофи та дефіси. Не дозволяє цифри."""
    # Дозволяємо кирилицю (\u0400-\u04FF), латиницю (a-zA-Z), пробіли (\s), дефіси (-) та апострофи (')
    if not re.match(r"^[a-zA-Z\s\u0400-\u04FF'-]+$", name):
        return False
    # Перевірка на мінімальну довжину і відсутність лише пробілів
    return len(name.strip()) > 0

def validate_phone(phone):
    """Перевіряє телефон: дозволяє форматування, але вимагає мінімум 7 цифр."""
    
    # 1. Перевірка на сторонні символи (заборона літер, спецсимволів крім дозволених)
    # Дозволені: цифри, пробіли, дефіси, дужки та знак +
    if not re.match(r"^[\d\s\-\(\)\+]+$", phone):
        return False
        
    # 2. Перевірка мінімальної кількості цифр
    # Видаляємо всі символи, крім цифр, і рахуємо їх
    digits_only = re.sub(r'[^\d]', '', phone)
    
    # Вимагаємо мінімум 7 цифр
    if len(digits_only) < 7:
        return False
        
    return True

def validate_email(email):
    """Базова перевірка email: перевіряє основний формат user@domain.tld."""
    # Спрощений regex для перевірки базової структури email
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)

# ============================================================
# ГОЛОВНА СТОРІНКА
# ============================================================

@app.route('/')
@login_required
def index():
    """Головна сторінка з загальною статистикою"""
    try:
        # Загальна статистика
        stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM customers) as total_customers,
                (SELECT COUNT(*) FROM employees) as total_employees,
                (SELECT COUNT(*) FROM menu_items) as total_menu_items,
                (SELECT COUNT(*) FROM orders WHERE order_status != 'CANCELLED') as total_orders,
                (SELECT COUNT(*) FROM orders WHERE order_status IN ('NEW', 'PREPARING', 'READY')) as active_orders,
                (SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0) 
                 FROM order_items oi 
                 INNER JOIN orders o ON oi.order_id = o.order_id 
                 WHERE o.order_status = 'PAID') as total_revenue
        """
        stats = db.execute_one(stats_query)
        
        # Останні замовлення
        recent_orders_query = """
            SELECT * FROM view_orders_full 
            ORDER BY order_time DESC 
            LIMIT 10
        """
        recent_orders = db.execute_query(recent_orders_query)
        
        return render_template('index.html', stats=stats, recent_orders=recent_orders)
    except Exception as e:
        flash(f'Помилка завантаження даних: {str(e)}', 'error')
        return render_template('index.html', stats=None, recent_orders=[])


# ============================================================
# МЕНЮ
# ============================================================

@app.route('/menu')
@login_required
def menu_list():
    """Список страв у меню з пошуком."""
    search_query = request.args.get('search', '').strip()
    
    base_sql = """
        SELECT mi.*, mc.category_name 
        FROM menu_items mi 
        JOIN menu_categories mc ON mi.category_id = mc.category_id
    """
    
    if search_query:
        sql = base_sql + " WHERE mi.menu_item_name ILIKE %s OR mi.menu_item_description ILIKE %s"
        search_param = f"%{search_query}%"
        items = db.execute_query(sql, (search_param, search_param))
    else:
        items = db.execute_query(base_sql)
    
    return render_template(
        'list.html',
        title='🍽️ Меню',
        items=items,
        columns=['ID', 'Назва', 'Категорія', 'Опис', 'Ціна'],
        fields=['menu_item_id', 'menu_item_name', 'category_name', 'menu_item_description', 'price'], # Зверніть увагу: category_name
        add_url='menu_add',
        edit_url='menu_edit',
        delete_url='menu_delete',
        id_field='menu_item_id',
        id_param='menu_item_id',
        search_query=search_query 
    )

@app.route('/menu/add', methods=['GET', 'POST'])
@role_required(['Адміністратор'])
def menu_add():
    """Додавання нової страви."""
    
    # 1. ЗАВАНТАЖЕННЯ КАТЕГОРІЙ
    category_data = db.execute_query("SELECT category_id, category_name FROM menu_categories ORDER BY category_name")
    category_options = [
        {'value': c['category_id'], 'label': c['category_name']} 
        for c in category_data
    ]
    
    # 2. ОНОВЛЕННЯ СТРУКТУРИ ПОЛІВ ФОРМИ
    fields_structure = [
        {'name': 'menu_item_name', 'label': 'Назва страви', 'type': 'text', 'required': True},
        {'name': 'category_id', 'label': 'Категорія', 'type': 'select', 'required': True, 'options': category_options}, # ЗМІНА
        {'name': 'menu_item_description', 'label': 'Опис', 'type': 'textarea', 'required': True},
        {'name': 'price', 'label': 'Ціна (грн)', 'type': 'number', 'required': True, 'step': '0.01', 'min': '0'},
    ]

    if request.method == 'POST':
        # ... (Валідація та отримання даних)
        name = request.form['menu_item_name']
        category_id = request.form['category_id'] # ЗМІНА: тепер ID
        description = request.form['menu_item_description']
        price = request.form['price']
        
        # ... (Валідація)

        # 3. ОНОВЛЕННЯ INSERT-ЗАПИТУ
        insert_query = """
            INSERT INTO menu_items (menu_item_name, category_id, menu_item_description, price) 
            VALUES (%s, %s, %s, %s)
        """
        try:
            db.execute(insert_query, (name, category_id, description, price), fetch=False)
            flash('Страву успішно додано!', 'success')
            return redirect(url_for('menu_list'))
        except Exception as e:
            # ... (Обробка помилки)
            # ...
            return render_template('form.html', title='➕ Додати страву', fields=fields_structure, back_url='menu_list')
    
    return render_template('form.html', title='➕ Додати страву', fields=fields_structure, back_url='menu_list')


@app.route('/menu/edit/<int:menu_item_id>', methods=['GET', 'POST'])
@role_required(['Адміністратор'])
def menu_edit(menu_item_id):
    """Редагування страви."""
    
    # 1. ЗАВАНТАЖЕННЯ КАТЕГОРІЙ
    category_data = db.execute_query("SELECT category_id, category_name FROM menu_categories ORDER BY category_name")
    category_options = [
        {'value': c['category_id'], 'label': c['category_name']} 
        for c in category_data
    ]

    # 2. ОНОВЛЕННЯ SELECT-ЗАПИТУ
    menu_item = db.execute_one(
        "SELECT * FROM menu_items WHERE menu_item_id = %s", 
        (menu_item_id,)
    )
    if not menu_item:
        flash("Страву не знайдено.", "error")
        return redirect(url_for('menu_list'))

    # 3. ОНОВЛЕННЯ СТРУКТУРИ ПОЛІВ ФОРМИ
    fields_structure = [
        {'name': 'menu_item_name', 'label': 'Назва страви', 'type': 'text', 'required': True, 'value': menu_item['menu_item_name']},
        {'name': 'category_id', 'label': 'Категорія', 'type': 'select', 'required': True, 
         'options': category_options, 'value': menu_item['category_id']}, # ЗМІНА
        {'name': 'menu_item_description', 'label': 'Опис', 'type': 'textarea', 'required': True, 'value': menu_item['menu_item_description']},
        {'name': 'price', 'label': 'Ціна (грн)', 'type': 'number', 'required': True, 'step': '0.01', 'min': '0', 'value': menu_item['price']},
    ]

    if request.method == 'POST':
        name = request.form['menu_item_name']
        category_id = request.form['category_id'] # ЗМІНА: тепер ID
        description = request.form['menu_item_description']
        price = request.form['price']
        

        # 4. ОНОВЛЕННЯ UPDATE-ЗАПИТУ
        update_query = """
            UPDATE menu_items SET menu_item_name=%s, category_id=%s, menu_item_description=%s, price=%s
            WHERE menu_item_id = %s
        """
        try:
            db.execute(update_query, (name, category_id, description, price, menu_item_id), fetch=False)
            flash('Дані страви успішно оновлено!', 'success')
            return redirect(url_for('menu_list'))
        except Exception as e:
            return render_template('form.html', title=f"✏️ Редагувати страву #{menu_item_id}", fields=fields_structure, back_url='menu_list')

    return render_template('form.html', title=f"✏️ Редагувати страву #{menu_item_id}", fields=fields_structure, back_url='menu_list')


@app.route('/menu/delete/<int:menu_item_id>')
@role_required(['Адміністратор'])
def menu_delete(menu_item_id):
    try:
        item = db.execute_one("SELECT menu_item_name FROM menu_items WHERE menu_item_id = %s", (menu_item_id,))
        db.execute_query("DELETE FROM menu_items WHERE menu_item_id = %s", (menu_item_id,), fetch=False)
        flash(f'Страву "{item["menu_item_name"]}" видалено!', 'success')
    except Exception as e:
        flash(f'Помилка видалення: {str(e)}', 'error')
    
    return redirect(url_for('menu_list'))


# ============================================================
# КЛІЄНТИ
# ============================================================

@app.route('/customers')
@login_required
def customers_list():
    customers = db.execute_query("""
        SELECT customer_id, first_name, last_name, phone, email
        FROM customers ORDER BY last_name, first_name
    """)
    
    return render_template('list.html',
        title='👥 Клієнти',
        items=customers,
        columns=['ID', "Ім'я", 'Прізвище', 'Телефон', 'Email'],
        fields=['customer_id', 'first_name', 'last_name', 'phone', 'email'],
        id_field='customer_id',
        id_param='customer_id',
        add_url='customers_add',
        delete_url='customers_delete'
    )


@app.route('/customers/add', methods=['GET', 'POST'])
def customers_add():
    if request.method == 'POST':
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            phone = request.form['phone']
            email = request.form['email']
            
            # --- ВАЛІДАЦІЯ (ДОДАНО) ---
            if not validate_name(first_name):
                flash("Помилка: Ім'я має містити лише літери, пробіли або дефіси. Цифри заборонені.", 'error')
                return redirect(url_for('customers_add'))
            if not validate_name(last_name):
                flash("Помилка: Прізвище має містити лише літери, пробіли або дефіси. Цифри заборонені.", 'error')
                return redirect(url_for('customers_add'))
            if not validate_phone(phone):
                flash("Помилка: Телефон містить недійсні символи. Дозволені: цифри, пробіли, +, -, (),", 'error')
                return redirect(url_for('customers_add'))
            if not validate_email(email):
                flash("Помилка: Email має невірний формат (приклад: user@domain.com).", 'error')
                return redirect(url_for('customers_add'))
            # --- КІНЕЦЬ ВАЛІДАЦІЇ ---
            
            query = """
                INSERT INTO customers (first_name, last_name, phone, email)
                VALUES (%s, %s, %s, %s)
            """
            db.execute_query(query, (
                first_name,
                last_name,
                phone,
                email
            ), fetch=False)
            flash('Клієнта додано!', 'success')
            return redirect(url_for('customers_list'))
        except Exception as e:
            flash(f'Помилка: {str(e)}', 'error')
            return redirect(url_for('customers_add')) # Повертаємо на форму у разі помилки
    
    fields = [
        {'name': 'first_name', 'label': "Ім'я", 'type': 'text', 'required': True},
        {'name': 'last_name', 'label': 'Прізвище', 'type': 'text', 'required': True},
        {'name': 'phone', 'label': 'Телефон', 'type': 'text', 'required': True},
        {'name': 'email', 'label': 'Email', 'type': 'text', 'required': True}
    ]
    
    return render_template('form.html',
        title='➕ Додати клієнта',
        fields=fields,
        back_url='customers_list'
    )


@app.route('/customers/delete/<int:customer_id>')
@role_required(['Адміністратор'])
def customers_delete(customer_id):
    try:
        customer = db.execute_one("SELECT first_name, last_name FROM customers WHERE customer_id = %s", (customer_id,))
        db.execute_query("DELETE FROM customers WHERE customer_id = %s", (customer_id,), fetch=False)
        flash(f'Клієнта "{customer["first_name"]} {customer["last_name"]}" видалено!', 'success')
    except Exception as e:
        flash(f'Помилка видалення: {str(e)}', 'error')
    
    return redirect(url_for('customers_list'))


# ============================================================
# ПРАЦІВНИКИ
# ============================================================

@app.route('/employees')
@login_required
def employees_list():
    """Список працівників."""
    query = """
    SELECT 
        e.employee_id,
        e.first_name,
        e.last_name,
        p.position_name AS position,
        e.phone,
        e.email,
        e.hire_date
        FROM employees e
        JOIN positions p ON e.position_id = p.position_id
    """
    employees = db.execute_query(query)
    
    return render_template(
        'list.html',
        title='🧑‍💼 Персонал',
        items=employees,
        columns=['ID', "Ім'я", 'Прізвище', 'Посада', 'Телефон', 'Email', 'Дата найму'],
        fields=['employee_id', 'first_name', 'last_name', 'position', 'phone', 'email', 'hire_date'],
        add_url='employees_add',
        delete_url='employees_delete',
        id_field='employee_id',
        id_param='employee_id'
    )


@app.route('/employees/add', methods=['GET', 'POST'])
@role_required(['Адміністратор'])
def employees_add():
    """Додавання нового працівника."""
    
    position_data = db.execute_query("SELECT position_id, position_name FROM positions ORDER BY position_name")
    
    position_options = [
        {'value': p['position_id'], 'label': p['position_name']} 
        for p in position_data
    ]
    
    fields_structure = [
        {'name': 'first_name', 'label': "Ім'я", 'type': 'text', 'required': True},
        {'name': 'last_name', 'label': 'Прізвище', 'type': 'text', 'required': True},
        {'name': 'position_id', 'label': 'Посада', 'type': 'select', 'required': True, 'options': position_options}, 
        {'name': 'phone', 'label': 'Телефон', 'type': 'text', 'required': True, 'placeholder': '+380...'},
        {'name': 'email', 'label': 'Email', 'type': 'text', 'required': True},
    ]

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        position_id = request.form['position_id'] 
        phone = request.form['phone']
        email = request.form['email']

        insert_query = """
            INSERT INTO employees (first_name, last_name, position_id, phone, email) 
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            db.execute(insert_query, (first_name, last_name, position_id, phone, email), fetch=False)
            flash('Працівника успішно додано!', 'success')
            return redirect(url_for('employees_list'))
        except Exception as e:
            flash(f"Помилка бази даних: {e}", 'error')
            # Повернення форми з помилкою
            for field in fields_structure:
                field['value'] = request.form.get(field['name'])
            return render_template('form.html', title='➕ Додати працівника', fields=fields_structure, back_url='employees_list')

    return render_template('form.html', title='➕ Додати працівника', fields=fields_structure, back_url='employees_list')


@app.route('/employees/delete/<int:employee_id>')
@role_required(['Адміністратор'])
def employees_delete(employee_id):
    try:
        employee = db.execute_one("SELECT first_name, last_name FROM employees WHERE employee_id = %s", (employee_id,))
        db.execute_query("DELETE FROM employees WHERE employee_id = %s", (employee_id,), fetch=False)
        flash(f'Працівника "{employee["first_name"]} {employee["last_name"]}" видалено!', 'success')
    except Exception as e:
        flash(f'Помилка видалення: {str(e)}', 'error')
    
    return redirect(url_for('employees_list'))


# ============================================================
# ЗАМОВЛЕННЯ
# ============================================================

@app.route('/orders')
@login_required
def orders_list():
    orders = db.execute_query("SELECT * FROM view_orders_full ORDER BY order_time DESC")
    
    return render_template('list.html',
        title='📝 Замовлення',
        items=orders,
        columns=['#', 'Час', 'Клієнт', 'Статус', 'Сума'],
        fields=['order_id', 'order_time', 'customer_name', 'order_status', 'total_amount'],
        id_field='order_id',
        id_param='order_id',
        delete_url='orders_delete'
    )

@app.route('/orders/add', methods=['GET', 'POST'])
def orders_add():
    """Створити нове замовлення"""
    if request.method == 'POST':
        try:
            customer_id = int(request.form['customer_id'])
            employee_id = int(request.form['employee_id'])
            table_id = int(request.form['table_id'])
            
            # Створити замовлення
            query = """
                INSERT INTO orders (customer_id, employee_id, table_id, order_status)
                VALUES (%s, %s, %s, 'NEW')
                RETURNING order_id
            """
            result = db.execute_one(query, (customer_id, employee_id, table_id))
            
            # ОНОВЛЕНО: Перенаправлення на сторінку деталей для додавання страв
            flash(f'Замовлення #{result["order_id"]} створено! Тепер додайте страви.', 'success')
            return redirect(url_for('orders_details', order_id=result['order_id']))
        except Exception as e:
            flash(f'Помилка: {str(e)}', 'error')
            return redirect(url_for('orders_add'))
    
    # GET - форма створення
    try:
        customers = db.execute_query("SELECT customer_id, first_name, last_name FROM customers ORDER BY last_name")
        employees = db.execute_query("""
            SELECT 
                e.employee_id, 
                e.first_name, 
                e.last_name 
            FROM 
                employees e
            INNER JOIN 
                positions p ON e.position_id = p.position_id
            WHERE 
                p.position_name = 'Офіціант' 
            ORDER BY 
                e.last_name
        """)
        
        # ОНОВЛЕНО: Запит для вибору лише вільних столів
        tables = db.execute_query("""
            SELECT table_id, seats, place 
            FROM restaurant_tables 
            WHERE is_active = TRUE 
            AND table_id NOT IN (
                SELECT table_id 
                FROM orders 
                WHERE order_status IN ('NEW', 'PREPARING', 'READY')
            )
            ORDER BY place, seats
        """)
        
        # Перевірка чи є дані
        if not customers:
            flash('Спочатку додайте клієнтів!', 'error')
            return redirect(url_for('customers_add'))
        
        if not employees:
            flash('Спочатку додайте офіціантів!', 'error')
            return redirect(url_for('employees_add'))
        
        if not tables:
            flash('Усі столи зайняті або в базі немає активних столів!', 'error')
            return redirect(url_for('index'))
        
        # Створюємо опції для select
        customer_options = [{'value': c['customer_id'], 'label': f"{c['first_name']} {c['last_name']}"} for c in customers]
        employee_options = [{'value': e['employee_id'], 'label': f"{e['first_name']} {e['last_name']}"} for e in employees]
        table_options = [{'value': t['table_id'], 'label': f"Стіл №{t['table_id']} ({t['place']}, {t['seats']} місць)"} for t in tables]
        
        fields = [
            {'name': 'customer_id', 'label': 'Клієнт', 'type': 'select', 'required': True, 'options': customer_options},
            {'name': 'employee_id', 'label': 'Офіціант', 'type': 'select', 'required': True, 'options': employee_options},
            {'name': 'table_id', 'label': 'Стіл', 'type': 'select', 'required': True, 'options': table_options}
        ]
        
        return render_template('form.html',
            title='➕ Створити замовлення',
            fields=fields,
            back_url='orders_list'
        )
    except Exception as e:
        flash(f'Помилка завантаження даних: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/orders/add_item/<int:order_id>', methods=['POST'])
def orders_add_item(order_id):
    """ДОДАНО: Обробка POST-запиту для додавання страви до замовлення."""
    try:
        menu_item_id = int(request.form['menu_item_id'])
        quantity = int(request.form['quantity'])
        
        if quantity <= 0:
            flash("Кількість має бути більше нуля.", "error")
            return redirect(url_for('orders_details', order_id=order_id))

        # Отримати ціну страви (якщо в базі ціна могла змінитися, беремо актуальну)
        item_price = db.execute_one("SELECT menu_item_name, price FROM menu_items WHERE menu_item_id = %s", (menu_item_id,))
        if not item_price:
            flash("Вибрана страва не знайдена.", "error")
            return redirect(url_for('orders_details', order_id=order_id))
            
        unit_price = item_price['price']

        # Додати позицію до замовлення
        query = """
            INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
        """
        db.execute_query(query, (order_id, menu_item_id, quantity, unit_price), fetch=False)
        
        flash(f'Страву "{item_price["menu_item_name"]}" у кількості {quantity} додано до замовлення #{order_id}!', 'success')
        
    except ValueError:
        flash("Некоректні дані: ID страви або кількість.", "error")
    except Exception as e:
        flash(f"Помилка додавання позиції: {str(e)}", "error")
        
    return redirect(url_for('orders_details', order_id=order_id))

@app.route('/orders/delete/<int:order_id>')
def orders_delete(order_id):
    try:
        # Видалити позиції, потім замовлення
        db.execute_query("DELETE FROM order_items WHERE order_id = %s", (order_id,), fetch=False)
        db.execute_query("DELETE FROM orders WHERE order_id = %s", (order_id,), fetch=False)
        flash(f'Замовлення #{order_id} видалено!', 'success')
    except Exception as e:
        flash(f'Помилка видалення: {str(e)}', 'error')
    
    return redirect(url_for('orders_list'))

@app.route('/orders/update_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    """Обробка POST-запиту для зміни статусу замовлення."""
    new_status = request.form.get('new_status')

    back_url = request.referrer if request.referrer else url_for('orders_list')
    
    if not new_status:
        flash("Не вказано новий статус.", "error")
        return redirect(back_url)

    valid_statuses = ['NEW', 'PREPARING', 'READY', 'PAID', 'CANCELLED']
    if new_status not in valid_statuses:
        flash(f"Невірний статус: {new_status}", "error")
        return redirect(back_url)

    try:
        query = "SELECT * FROM update_order_status(%s, %s)"
        result = db.execute_query(query, (order_id, new_status), fetch=True)
        
        if result and result[0]['old_status'] != new_status:
            flash(f"Статус замовлення №{order_id} успішно змінено з **{result[0]['old_status']}** на **{new_status}**.", "success")
        elif result:
             flash(f"Статус замовлення №{order_id} вже був **{new_status}**.", "info")
        else:
             flash(f"Помилка: Замовлення №{order_id} не знайдено або не змінено.", "error")

    except Exception as e:
        flash(f"Помилка зміни статусу: {e!s}", "error")

    return redirect(back_url)


@app.route('/orders/<int:order_id>')
def orders_details(order_id):
    """Відображення деталей одного замовлення."""
    order_query = "SELECT * FROM view_orders_full WHERE order_id = %s"
    items_query = """
        SELECT oi.order_item_id, mi.menu_item_name, oi.quantity, oi.unit_price, (oi.quantity * oi.unit_price) as total_item_price
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.menu_item_id
        WHERE oi.order_id = %s
    """
    
    order = db.execute_one(order_query, (order_id,))
    items = db.execute_query(items_query, (order_id,))
    
    if not order:
        flash(f"Замовлення №{order_id} не знайдено.", "error")
        return redirect(url_for('orders_list'))

    menu_items = db.execute_query("SELECT menu_item_id, menu_item_name, price FROM menu_items ORDER BY menu_item_name")
    
    # Визначення всіх можливих статусів
    statuses = ['NEW', 'PREPARING', 'READY', 'PAID', 'CANCELLED']
        
    return render_template(
        'order_details.html',
        order=order,
        items=items,
        statuses=statuses,
        menu_items=menu_items, # Передаємо список страв
        title=f"Деталі замовлення №{order_id}"
    )

# ============================================================
# СТАТИСТИКА
# ============================================================

@app.route('/statistics')
@login_required
def statistics():
    """Сторінка зі статистикою"""
    try:
        # Популярні страви
        popular = db.execute_query("""
            SELECT * FROM view_popular_dishes LIMIT 10
        """)
        
        # Статистика працівників
        employees = db.execute_query("""
            SELECT * FROM view_employee_statistics 
            ORDER BY total_revenue DESC
        """)

        last_30_days = db.execute_one("""
            SELECT * FROM view_stats_last_30_days
        """)
        
        # Якщо немає даних
        if not popular:
            popular = []
        if not employees:
            employees = []
        
        return render_template('statistics.html',
            popular_dishes=popular,
            employee_stats=employees,
            last_30_days=last_30_days
        )
    except Exception as e:
        flash(f'Помилка завантаження статистики: {str(e)}', 'error')
        return render_template('statistics.html',
            popular_dishes=[],
            employee_stats=[]
        )


@app.route('/reports')
@login_required
def reports():
    """Сторінка звітів"""
    return redirect(url_for('statistics'))

@app.route('/test-db')
def test_db():
    """Тест даних в БД"""
    try:
        stats = {
            'customers': db.execute_query("SELECT COUNT(*) as count FROM customers")[0]['count'],
            'employees': db.execute_query("SELECT COUNT(*) as count FROM employees")[0]['count'],
            'menu_items': db.execute_query("SELECT COUNT(*) as count FROM menu_items")[0]['count'],
            'orders': db.execute_query("SELECT COUNT(*) as count FROM orders")[0]['count'],
            'tables': db.execute_query("SELECT COUNT(*) as count FROM restaurant_tables")[0]['count'],
        }
        
        return f"""
        <h1>Статистика БД</h1>
        <ul>
            <li>Клієнтів: {stats['customers']}</li>
            <li>Працівників: {stats['employees']}</li>
            <li>Страв у меню: {stats['menu_items']}</li>
            <li>Замовлень: {stats['orders']}</li>
            <li>Столів: {stats['tables']}</li>
        </ul>
        <a href="/">Назад на головну</a>
        """
    except Exception as e:
        return f"<h1>Помилка: {e}</h1><a href='/'>Назад</a>"

# ============================================================
# ЗВІТ
# ============================================================

@app.route('/reports/download/revenue')
@login_required
@role_required(['Адміністратор'])
def download_revenue_report():
    employees = db.execute_query("SELECT * FROM view_employee_statistics ORDER BY total_revenue DESC")
    
    # Створення CSV в пам'яті
    si = StringIO()
    cw = csv.writer(si)
    
    # Заголовки
    cw.writerow(['ID', 'Ім\'я', 'Посада', 'Кількість замовлень', 'Виручка (грн)'])
    
    # Дані
    for emp in employees:
        cw.writerow([
            emp['employee_id'], 
            emp['employee_name'], 
            emp['position'], 
            emp['total_orders'], 
            emp['total_revenue']
        ])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=employees_report.csv"}
    )

@app.route('/reports/download/dishes')
@login_required
@role_required(['Адміністратор'])
def download_dishes_report():
    """Генерація CSV файлу зі звітом про популярність страв"""
    dishes = db.execute_query("SELECT * FROM view_popular_dishes ORDER BY times_ordered DESC")
    
    # Створення CSV в пам'яті
    si = StringIO()
    
    # Додаємо BOM для коректного відображення кирилиці в Excel
    si.write('\ufeff')
    
    cw = csv.writer(si)
    
    # Заголовки
    cw.writerow(['Назва страви', 'Категорія', 'Замовлено разів', 'Загальна виручка (грн)'])
    
    # Дані
    for dish in dishes:
        cw.writerow([
            dish['menu_item_name'], 
            dish['category'], 
            dish['times_ordered'], 
            dish['total_revenue']
        ])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=menu_popularity_report.csv"}
    )

# ============================================================
# ЛОГУВАННЯ
# ============================================================

@app.route('/audit')
@login_required
@role_required(['Адміністратор'])
def audit_log():
    """Перегляд логу змін статусів замовлень"""
    logs = db.execute_query("""
        SELECT * FROM order_audit 
        ORDER BY changed_at DESC 
        LIMIT 50
    """)
    
    return render_template('list.html',
        title='🕵️ Лог операцій',
        items=logs,
        columns=['ID', 'Замовлення', 'Дія', 'Старий статус', 'Новий статус', 'Хто змінив', 'Час'],
        fields=['audit_id', 'order_id', 'action', 'old_status', 'new_status', 'changed_by', 'changed_at'],
        id_field='audit_id'
    )

# ============================================================
# ЗАПУСК ДОДАТКУ
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)