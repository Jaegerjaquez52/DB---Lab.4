# Dockerfile

# Використовуємо офіційний образ Python
# Залишимо slim, але додамо інструменти
FROM python:3.11-slim

# Встановлюємо робочий каталог у контейнері
WORKDIR /app

# ----------------------------------------------------
# ДОДАННЯ СИСТЕМНИХ ЗАЛЕЖНОСТЕЙ ДЛЯ PSYCOPG/LIBPQ
# Встановлення пакетів для компіляції та libpq
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        # Потрібно для libpq-dev
        libpq-dev \
        # Потрібно для компіляції C-розширень Python
        gcc \
        # Потрібно для компіляції C-розширень Python
        python3-dev \
    && rm -rf /var/lib/apt/lists/*
# ----------------------------------------------------

# Копіюємо файл залежностей та встановлюємо їх
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо всі файли проекту (app.py, database.py, папка templates, тощо)
COPY . .

# Виставляємо порт, який буде використовувати Flask
EXPOSE 5000

# Команда для запуску додатка
CMD ["python", "app.py"]