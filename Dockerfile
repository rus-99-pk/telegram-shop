# --- Этап 1: Сборщик (Builder) ---
# Здесь мы устанавливаем зависимости, используя полный образ python
FROM python:3.12-slim AS builder

WORKDIR /app_build

COPY requirements.txt .
# Устанавливаем зависимости в отдельную директорию, которая будет скопирована в финальный образ
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt

# --- Этап 2: Финальный образ ---
FROM python:3.12-slim

# Создаем пользователя и группу 'app'
RUN groupadd -r app && useradd -r -g app app

WORKDIR /bot

# Копируем только установленные пакеты из этапа сборки
COPY --from=builder /install /usr/local

# Копируем код нашего приложения
COPY ./app ./app

# Создаем директорию для базы данных и меняем владельца всего рабочего каталога
# Это позволит пользователю 'app' создавать и писать в файл БД внутри /bot/db
RUN mkdir /bot/db && chown -R app:app /bot

# Переключаемся на непривилегированного пользователя 'app'
USER app

# Указываем команду для запуска. Обратите внимание на новый путь к БД ниже!
CMD ["python", "-m", "app.bot"]