# Магазин в Telegram

Это полнофункциональный асинхронный телеграм-бот для организации продаж товаров. Бот предоставляет удобный интерфейс как для покупателей, так и для администраторов магазина. Он построен на современных технологиях, включая Aiogram 3, SQLAlchemy 2.0 и Docker.

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-orange.svg)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)

## Основные возможности

### Для пользователей:
- 🛍️ **Каталог товаров:** Просмотр товаров с пагинацией.
- 🖼️ **Детальная информация:** Просмотр карточки товара с фото, описанием и ценой.
- 🛒 **Корзина:** Добавление товаров в корзину, просмотр содержимого и итоговой суммы.
- 📝 **Оформление заказа:** Пошаговый процесс оформления заказа с указанием:
    - Пункта выдачи СДЭК.
    - ФИО получателя.
    - Контактного номера телефона.
- 💳 **Оплата:** Процесс "псевдо-оплаты" через отправку чека (PDF-файла) после перевода на карту.
- 📜 **История заказов:** Просмотр списка своих заказов и их статусов.
- 🚚 **Отслеживание:** Возможность отследить заказ по трек-номеру СДЭК, если он добавлен администратором.
- ✅ **Подтверждение получения:** Пользователь может подтвердить получение заказа, завершая сделку.
- 💬 **Поддержка:** Прямая ссылка на аккаунт поддержки.

### Для администраторов:
- 🔐 **Панель администратора:** Отдельное меню с расширенными функциями, доступное только администраторам.
- ➕ **Управление товарами:**
    - Добавление новых товаров (название, цена, фото, описание).
    - Редактирование существующих товаров (изменение цены, названия, описания).
    - Удаление товаров.
- 📋 **Управление заказами:**
    - Просмотр списка всех заказов в боте.
    - Просмотр полной информации по каждому заказу (данные клиента, состав, сумма).
    - Изменение статуса заказа (`В работе`, `Отправлен`, `Завершен`, `Отменен`).
    - Просмотр прикрепленного пользователем чека об оплате.
- 🚀 **Отправка заказов:** Добавление трек-номера СДЭК к заказу, с автоматическим уведомлением пользователя.
- 📊 **Статистика:** Просмотр основной статистики магазина:
    - Общее количество пользователей.
    - Количество заказов по статусам.
    - Общая выручка по завершенным заказам.
- 📈 **Генерация отчетов:** Выгрузка подробного отчета по всем заказам в формате Excel.
- 📢 **Рассылка:** Отправка сообщений всем пользователям бота с поддержкой HTML-форматирования.

## Технологический стек

- **Python 3.12**
- **Aiogram 3.x:** Асинхронный фреймворк для создания телеграм-ботов.
- **SQLAlchemy 2.0 (AsyncIO):** Работа с базой данных в асинхронном режиме.
- **AioSQLite:** Асинхронный драйвер для работы с SQLite.
- **Pydantic (pydantic-settings):** Удобная и строгая валидация конфигурации через переменные окружения.
- **Openpyxl:** Библиотека для создания и чтения Excel-файлов (используется для генерации отчетов).
- **Docker & Docker Compose:** Контейнеризация и оркестрация для легкого развертывания.

## Установка и запуск

Проект разработан для запуска в Docker-контейнере, что значительно упрощает развертывание.

### 1. Клонирование репозитория

```bash
git clone https://github.com/rus-99-pk/telegram-shop.git
cd telegram-shop
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корневой директории проекта, скопировав в него содержимое из `.env.example`, и заполните его своими данными.

```dotenv
# .env

# Токен вашего бота, полученный у @BotFather
BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

# Список Telegram ID администраторов в формате JSON-массива
ADMIN_IDS="[123456789, 987654321]"

# Имя пользователя (username) для связи с поддержкой (без @)
SUPPORT_USERNAME="support_user"

# Telegram ID разработчика для получения уведомлений об ошибках
DEVELOPER_ID="123456789"

# Номер банковской карты для приема платежей
BANK_CARD_NUMBER="0000 0000 0000 0000"

# Владелец банковской карты для приема платежей
BANK_CARD_OWNER="Андрей А."
```
> **Важно:** `ADMIN_IDS` должен быть строкой, содержащей список чисел в формате JSON.

### 3. Запуск

Убедитесь, что у вас установлены **Docker** и **Docker Compose**.
Для удобства в проекте есть готовые shell-скрипты.

**Чтобы запустить бота:**
(Скрипт автоматически создаст файл `database.db`, если он отсутствует, и соберет/запустит контейнеры)
```bash
chmod +x ./scripts/start.sh
./scripts/start.sh
```
Для запуска в фоновом режиме (detached mode):
```bash
./scripts/start.sh -d
```

**Чтобы остановить бота:**
```bash
chmod +x ./scripts/stop.sh
./scripts/stop.sh
```

**Чтобы остановить и полностью удалить все данные (контейнеры и базу данных):**
**ВНИМАНИЕ! Эта команда безвозвратно удалит `database.db`!**
```bash
chmod +x ./scripts/wipe_all.sh
./scripts/wipe_all.sh
```

## Структура проекта

```
.
├── app/                  # Основная папка с кодом бота
│   ├── database/         # Модули для работы с базой данных
│   │   ├── models.py     # Модели SQLAlchemy
│   │   └── requests.py   # Функции для запросов к БД (CRUD)
│   ├── handlers/         # Обработчики сообщений и колбэков
│   │   ├── admin.py      # Логика для администраторов
│   │   └── user.py       # Логика для обычных пользователей
│   ├── keyboards/        # Модули для создания клавиатур
│   │   ├── builders.py   # Inline-клавиатуры
│   │   └── reply.py      # Reply-клавиатуры
│   ├── services/         # Вспомогательные сервисы
│   │   ├── notifications.py      # Отправка уведомлений
│   │   └── report_generator.py # Генерация Excel-отчетов
│   ├── bot.py            # Точка входа в приложение, инициализация бота и диспетчера
│   ├── config.py         # Конфигурация Pydantic
│   └── lexicon/          # Текстовые ресурсы
│       └── lexicon_ru.py # Все тексты и сообщения бота
├── scripts/              # Вспомогательные скрипты для управления
│   ├── start.sh
│   ├── stop.sh
│   └── wipe_all.sh
├── .env.example          # Пример файла с переменными окружения
├── .gitignore            # Файлы, исключенные из контроля версий
├── Dockerfile            # Инструкции для сборки Docker-образа
├── docker-compose.yaml   # Конфигурация для запуска контейнера
└── requirements.txt      # Список зависимостей Python
```