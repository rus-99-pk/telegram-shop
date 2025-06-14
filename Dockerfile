# Dockerfile

FROM python:3.12-slim

WORKDIR /bot

# Создаем пользователя и группу 'app'
RUN groupadd -r app && useradd -r -g app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

# Меняем владельца директории
RUN chown -R app:app /bot

# Переключаемся на пользователя 'app'
USER app

CMD ["python", "-m", "app.bot"]