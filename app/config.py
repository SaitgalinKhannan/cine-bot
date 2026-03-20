from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения через переменные окружения"""

    # Telegram
    bot_token: str
    group_chat_id: int

    # PostgreSQL
    postgres_user: str
    postgres_password: str
    postgres_db: str
    database_url: str

    # Яндекс.Диск
    yandex_disk_token: str
    yadisk_debug: bool = False

    # LLM (OpenRouter)
    openrouter_api_key: str | None = None
    llm_model: str = "openrouter/hunter-alpha"
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_trigger_words: str = "добавить,добавь,найти,найди,покажи,покажите,удалить,удали,создать,создай,запланировать,запланируй,искать,ищи,отменить,отмени,список,события"

    # Admin users (comma-separated telegram IDs)
    admin_telegram_ids: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def admin_ids_list(self) -> list[int]:
        """Получить список ID администраторов"""
        if not self.admin_telegram_ids:
            return []
        return [int(id.strip()) for id in self.admin_telegram_ids.split(",") if id.strip()]

    @property
    def trigger_words_list(self) -> list[str]:
        """Получить список триггерных слов для LLM-агента"""
        return [word.strip().lower() for word in self.llm_trigger_words.split(",") if word.strip()]


settings = Settings()
