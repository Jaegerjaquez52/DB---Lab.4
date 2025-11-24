from flask import Flask, render_template, request, redirect, url_for, flash
from database import DatabaseConnection

# Ініціалізація Flask додатку
app = Flask(__name__)
app.secret_key = '12345'



# Підключення до бази даних
db = DatabaseConnection(
    dbname='restaurant',
    user='postgres',
    password='password',
    host='postgres',
    port=5432
)
db.connect()

# ============================================================
# ГОЛОВНА СТОРІНКА
# ============================================================

@app.route('/')
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
            LIMIT 5
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
def menu_list():
    menu_items = db.execute_query("""
        SELECT menu_item_id, menu_item_name, category, price
        FROM menu_items ORDER BY category, menu_item_name
    """)
    
    return render_template('list.html',
        title='📋 Меню ресторану',
        items=menu_items,
        columns=['ID', 'Назва', 'Категорія', 'Ціна'],
        fields=['menu_item_id', 'menu_item_name', 'category', 'price'],
        id_field='menu_item_id',
        id_param='menu_item_id',
        add_url='menu_add',
        edit_url='menu_edit',
        delete_url='menu_delete'
    )

@app.route('/menu/add', methods=['GET', 'POST'])
def menu_add():
    if request.method == 'POST':
        try:
            name = request.form['name']
            category = request.form['category']
            description = request.form['description']
            price = float(request.form['price'])
            
            query = """
                INSERT INTO menu_items (menu_item_name, category, menu_item_description, price)
                VALUES (%s, %s, %s, %s)
            """
            db.execute_query(query, (name, category, description, price), fetch=False)
            flash(f'Страву "{name}" додано!', 'success')
            return redirect(url_for('menu_list'))
        except Exception as e:
            flash(f'Помилка: {str(e)}', 'error')
    
    fields = [
        {'name': 'name', 'label': 'Назва страви', 'type': 'text', 'required': True},
        {'name': 'category', 'label': 'Категорія', 'type': 'select', 'required': True,
         'options': [{'value': c, 'label': c} for c in ['Супи', 'Салати', 'Гарячі страви', 'Паста', 'Десерти', 'Напої', 'Алкоголь']]},
        {'name': 'description', 'label': 'Опис', 'type': 'textarea', 'required': False},
        {'name': 'price', 'label': 'Ціна (грн)', 'type': 'number', 'required': True, 'step': '0.01', 'min': '0.01'}
    ]
    
    return render_template('form.html',
        title='➕ Додати страву',
        fields=fields,
        back_url='menu_list'
    )


@app.route('/menu/edit/<int:menu_item_id>', methods=['GET', 'POST'])
def menu_edit(menu_item_id):
    if request.method == 'POST':
        try:
            name = request.form['name']
            category = request.form['category']
            description = request.form['description']
            price = float(request.form['price'])
            
            query = """
                UPDATE menu_items 
                SET menu_item_name = %s, category = %s, 
                    menu_item_description = %s, price = %s
                WHERE menu_item_id = %s
            """
            db.execute_query(query, (name, category, description, price, menu_item_id), fetch=False)
            flash(f'Страву "{name}" оновлено!', 'success')
            return redirect(url_for('menu_list'))
        except Exception as e:
            flash(f'Помилка: {str(e)}', 'error')
    
    # GET - отримати дані страви
    item = db.execute_one("SELECT * FROM menu_items WHERE menu_item_id = %s", (menu_item_id,))
    
    if not item:
        flash('Страву не знайдено', 'error')
        return redirect(url_for('menu_list'))
    
    fields = [
        {'name': 'name', 'label': 'Назва страви', 'type': 'text', 'required': True, 
         'value': item['menu_item_name']},
        {'name': 'category', 'label': 'Категорія', 'type': 'select', 'required': True,
         'value': item['category'],
         'options': [{'value': c, 'label': c} for c in ['Супи', 'Салати', 'Гарячі страви', 'Паста', 'Десерти', 'Напої', 'Алкоголь']]},
        {'name': 'description', 'label': 'Опис', 'type': 'textarea', 'required': False,
         'value': item['menu_item_description']},
        {'name': 'price', 'label': 'Ціна (грн)', 'type': 'number', 'required': True, 
         'step': '0.01', 'min': '0.01', 'value': item['price']}
    ]
    
    return render_template('form.html',
        title='✏️ Редагувати страву',
        fields=fields,
        back_url='menu_list'
    )


@app.route('/menu/delete/<int:menu_item_id>')
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
            query = """
                INSERT INTO customers (first_name, last_name, phone, email)
                VALUES (%s, %s, %s, %s)
            """
            db.execute_query(query, (
                request.form['first_name'],
                request.form['last_name'],
                request.form['phone'],
                request.form['email']
            ), fetch=False)
            flash('Клієнта додано!', 'success')
            return redirect(url_for('customers_list'))
        except Exception as e:
            flash(f'Помилка: {str(e)}', 'error')
    
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
def employees_list():
    employees = db.execute_query("""
        SELECT employee_id, first_name, last_name, position, phone, email
        FROM employees ORDER BY position, last_name
    """)
    
    return render_template('list.html',
        title='👔 Працівники',
        items=employees,
        columns=['ID', "Ім'я", 'Прізвище', 'Посада', 'Телефон', 'Email'],
        fields=['employee_id', 'first_name', 'last_name', 'position', 'phone', 'email'],
        id_field='employee_id',
        id_param='employee_id',
        add_url='employees_add',
        delete_url='employees_delete'
    )


@app.route('/employees/add', methods=['GET', 'POST'])
def employees_add():
    if request.method == 'POST':
        try:
            query = """
                INSERT INTO employees (first_name, last_name, position, phone, email)
                VALUES (%s, %s, %s, %s, %s)
            """
            db.execute_query(query, (
                request.form['first_name'],
                request.form['last_name'],
                request.form['position'],
                request.form['phone'],
                request.form['email']
            ), fetch=False)
            flash('Працівника додано!', 'success')
            return redirect(url_for('employees_list'))
        except Exception as e:
            flash(f'Помилка: {str(e)}', 'error')
    
    fields = [
        {'name': 'first_name', 'label': "Ім'я", 'type': 'text', 'required': True},
        {'name': 'last_name', 'label': 'Прізвище', 'type': 'text', 'required': True},
        {'name': 'position', 'label': 'Посада', 'type': 'select', 'required': True,
         'options': [{'value': p, 'label': p} for p in ['Офіціант', 'Кухар', 'Адміністратор', 'Бармен']]},
        {'name': 'phone', 'label': 'Телефон', 'type': 'text', 'required': True},
        {'name': 'email', 'label': 'Email', 'type': 'text', 'required': True}
    ]
    
    return render_template('form.html',
        title='➕ Додати працівника',
        fields=fields,
        back_url='employees_list'
    )


@app.route('/employees/delete/<int:employee_id>')
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
            
            flash(f'Замовлення #{result["order_id"]} створено!', 'success')
            return redirect(url_for('orders_list'))
        except Exception as e:
            flash(f'Помилка: {str(e)}', 'error')
            return redirect(url_for('orders_add'))
    
    # GET - форма створення
    try:
        customers = db.execute_query("SELECT customer_id, first_name, last_name FROM customers ORDER BY last_name")
        employees = db.execute_query("SELECT employee_id, first_name, last_name FROM employees WHERE position = 'Офіціант' ORDER BY last_name")
        tables = db.execute_query("SELECT table_id, seats, place FROM restaurant_tables WHERE is_active = TRUE ORDER BY place, seats")
        
        # Перевірка чи є дані
        if not customers:
            flash('Спочатку додайте клієнтів!', 'error')
            return redirect(url_for('customers_add'))
        
        if not employees:
            flash('Спочатку додайте офіціантів!', 'error')
            return redirect(url_for('employees_add'))
        
        if not tables:
            flash('В базі немає активних столів!', 'error')
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


# ============================================================
# СТАТИСТИКА
# ============================================================

@app.route('/statistics')
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
        
        # Якщо немає даних
        if not popular:
            popular = []
        if not employees:
            employees = []
        
        return render_template('statistics.html',
            popular_dishes=popular,
            employee_stats=employees
        )
    except Exception as e:
        flash(f'Помилка завантаження статистики: {str(e)}', 'error')
        return render_template('statistics.html',
            popular_dishes=[],
            employee_stats=[]
        )


@app.route('/reports')
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
# ЗАПУСК ДОДАТКУ
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)