#!/usr/bin/env python3
"""
Скрипт для быстрой проверки работоспособности бота
Запускается локально без Docker для тестирования
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))


async def test_imports():
    """Проверка импортов всех модулей"""
    print("🔍 Проверка импортов...")

    try:
        from app.config import settings
        print("✅ app.config")
    except Exception as e:
        print(f"❌ app.config: {e}")
        return False

    try:
        from app.db.base import Base, engine, async_session_maker
        print("✅ app.db.base")
    except Exception as e:
        print(f"❌ app.db.base: {e}")
        return False

    try:
        from app.db.models import Event, YandexFileCache
        print("✅ app.db.models")
    except Exception as e:
        print(f"❌ app.db.models: {e}")
        return False

    try:
        from app.states.event_states import AddEventFSM, DeleteEventFSM
        print("✅ app.states.event_states")
    except Exception as e:
        print(f"❌ app.states.event_states: {e}")
        return False

    try:
        from app.services.event_service import EventService
        print("✅ app.services.event_service")
    except Exception as e:
        print(f"❌ app.services.event_service: {e}")
        return False

    try:
        from app.services.reminder_service import ReminderService
        print("✅ app.services.reminder_service")
    except Exception as e:
        print(f"❌ app.services.reminder_service: {e}")
        return False

    try:
        from app.services.yadisk_service import YandexDiskService
        print("✅ app.services.yadisk_service")
    except Exception as e:
        print(f"❌ app.services.yadisk_service: {e}")
        return False

    try:
        from app.handlers import common, events, files
        print("✅ app.handlers")
    except Exception as e:
        print(f"❌ app.handlers: {e}")
        return False

    try:
        from app.scheduler import setup_scheduler
        print("✅ app.scheduler")
    except Exception as e:
        print(f"❌ app.scheduler: {e}")
        return False

    return True


async def test_config():
    """Проверка конфигурации"""
    print("\n🔍 Проверка конфигурации...")

    try:
        from app.config import settings

        # Проверяем обязательные поля
        required_fields = [
            'bot_token',
            'group_chat_id',
            'postgres_user',
            'postgres_password',
            'postgres_db',
            'database_url',
            'yandex_disk_token'
        ]

        for field in required_fields:
            value = getattr(settings, field)
            if value and not str(value).startswith('your_') and 'xxxx' not in str(value):
                print(f"✅ {field}: настроен")
            else:
                print(f"⚠️  {field}: требует настройки")

        return True
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False


async def test_database_models():
    """Проверка моделей базы данных"""
    print("\n🔍 Проверка моделей БД...")

    try:
        from app.db.models import Event, YandexFileCache
        from app.db.base import Base

        # Проверяем, что модели наследуются от Base
        assert issubclass(Event, Base), "Event должен наследоваться от Base"
        assert issubclass(YandexFileCache, Base), "YandexFileCache должен наследоваться от Base"

        # Проверяем наличие таблиц
        assert Event.__tablename__ == "events"
        assert YandexFileCache.__tablename__ == "yandex_files_cache"

        print("✅ Модель Event")
        print("✅ Модель YandexFileCache")

        return True
    except Exception as e:
        print(f"❌ Ошибка моделей: {e}")
        return False


async def main():
    """Главная функция тестирования"""
    print("🤖 CineBot - Проверка работоспособности\n")

    results = []

    # Тест 1: Импорты
    results.append(await test_imports())

    # Тест 2: Конфигурация
    results.append(await test_config())

    # Тест 3: Модели БД
    results.append(await test_database_models())

    # Итоги
    print("\n" + "="*50)
    if all(results):
        print("✅ Все проверки пройдены успешно!")
        print("\n📋 Следующие шаги:")
        print("1. Убедитесь, что .env заполнен реальными токенами")
        print("2. Запустите: docker compose up -d")
        print("3. Проверьте логи: docker compose logs -f bot")
        return 0
    else:
        print("❌ Некоторые проверки не прошли")
        print("\nИсправьте ошибки и запустите снова:")
        print("python test_setup.py")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
