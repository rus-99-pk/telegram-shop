#!/bin/bash
echo "!!! ВНИМАНИЕ: СЕЙЧАС БУДУТ УДАЛЕНЫ ВСЕ ДАННЫЕ !!!"

echo "Останавливаю и удаляю контейнеры..."
docker-compose down

echo "Очищаю систему Docker (образы, сети, кэш)..."
docker system prune -af

echo "Очищаю Docker volumes..."
docker volume prune -af

# Явное удаление файла базы данных!
if [ -f ./database.db ]; then
    echo "Удаляю локальный файл базы данных (database.db)..."
    rm ./database.db
fi

echo "Полная очистка завершена."