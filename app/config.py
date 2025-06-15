from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

# Класс для хранения настроек приложения, загружаемых из .env файла
class Settings(BaseSettings):
    bot_token: SecretStr  # Токен Telegram бота (скрытый тип, не будет отображаться в логах)
    admin_ids: list[int]  # Список Telegram ID администраторов
    developer_id: int     # Telegram ID разработчика для получения уведомлений об ошибках
    support_username: str # Имя пользователя для связи с поддержкой (без @)
    bank_card_number: str # Номер банковской карты для приема платежей
    bank_card_owner: str  # Владелец банковской карты для приема платежей

    # Конфигурация для загрузки настроек из файла .env
    model_config = SettingsConfigDict(
        env_file=(
            '/run/secrets/app_config_secret', # Для Docker
            '.env'                            # Для локального запуска (pydantic проверит оба)
        ),
        env_file_encoding='utf-8'  # Кодировка файла
    )

# Создаем экземпляр настроек, который будет использоваться во всем приложении
config = Settings()