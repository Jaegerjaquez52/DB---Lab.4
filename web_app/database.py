import psycopg
from psycopg.rows import dict_row


class DatabaseConnection:
    """Клас для управління підключенням до PostgreSQL"""

    def __init__(self, dbname='restaurant', user='postgres',
                 password='password', host='localhost', port=5432):
        self.conn_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
        self.conn: psycopg.Connection | None = None

    def connect(self) -> bool:
        """Встановити з'єднання з базою даних"""
        try:
            self.conn = psycopg.connect(
                dbname=self.conn_params['dbname'],
                user=self.conn_params['user'],
                password=self.conn_params['password'],
                host=self.conn_params['host'],
                port=self.conn_params['port'],
                autocommit=False,
                options='-c client_encoding=UTF8',
                row_factory=dict_row,  
            )
            print("Успішне підключення до бази даних")
            return True
        except Exception as e:
        
            print(f"Помилка підключення: {e!s}")
            self.conn = None
            return False

    def disconnect(self):
        """Закрити з'єднання з базою даних"""
        if self.conn is not None and not self.conn.closed:
            self.conn.close()
            self.conn = None

    def _ensure_connection(self) -> bool:
        """Перевірити та відновити підключення якщо потрібно"""
        if self.conn is None or self.conn.closed:
            print("З'єднання втрачено, відновлюємо...")
            self.connect()
        return self.conn is not None and not self.conn.closed

    def execute_query(self, query: str, params=None, fetch: bool = True):
        """
        Виконати SQL-запит

        Args:
            query: SQL-запит
            params: параметри запиту (tuple/list або dict)
            fetch: чи потрібно отримати результат

        Returns:
            list[dict] або None
        """
        if not self._ensure_connection():
            print("Немає підключення до БД")
            return None if fetch else False

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                if fetch:
                    result = cur.fetchall()  # завдяки row_factory це буде list[dict]
                    self.conn.commit()
                    return result
                else:
                    self.conn.commit()
                    return True
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"Помилка виконання запиту: {e!s}")
            print(f"Запит: {query}")
            raise

    def execute_one(self, query: str, params=None):
        """Виконати запит і отримати один запис (dict або None)"""
        if not self._ensure_connection():
            print("Немає підключення до БД")
            return None

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                self.conn.commit()
                return row
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"Помилка виконання запиту: {e!s}")
            print(f"Запит: {query}")
            raise
