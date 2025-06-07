# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию на уровень выше, чем папка с кодом
WORKDIR /bot

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем папку app целиком в контейнер
COPY ./app ./app

CMD ["python", "-m", "app.bot"]