#!/bin/bash
echo "!!! ВНИМАНИЕ: СЕЙЧАС БУДУТ УДАЛЕНЫ ВСЕ ДАННЫЕ !!!"

echo "Останавливаю и удаляю контейнеры..."
docker compose down

# Явное удаление файла базы данных!
if [ -f ./database.db ]; then
    echo "Удаляю локальный файл базы данных (database.db)..."
    rm ./database.db
fi

echo "Полная очистка завершена."