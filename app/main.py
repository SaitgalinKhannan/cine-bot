import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from app.config import settings
from app.db.base import engine
from app.db.models import Base
from app.handlers import common, events, files, llm, admin
from app.middleware.auth import AuthMiddleware
from app.scheduler import setup_scheduler


async def on_startup():
    """Действия при запуске бота"""
    logger.info("Starting CineBot...")

    # Создание таблиц (если их нет)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Shutting down CineBot...")
    await engine.dispose()


async def main():
    """Главная функция запуска бота"""
    # Настройка логирования
    logger.add(
        "logs/bot.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )

    # Инициализация бота и диспетчера
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация middleware
    dp.message.middleware(AuthMiddleware())

    # Регистрация роутеров
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(events.router)
    dp.include_router(files.router)
    # LLM handler должен быть последним (обрабатывает все текстовые сообщения)
    dp.include_router(llm.router)

    # Регистрация команд в меню
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Справка по командам"),
        BotCommand(command="addevent", description="Добавить событие"),
        BotCommand(command="events", description="Ближайшие события"),
        BotCommand(command="delevent", description="Удалить событие"),
        BotCommand(command="find", description="Найти файл на Яндекс.Диске"),
        BotCommand(command="addemployee", description="[Админ] Добавить сотрудника"),
        BotCommand(command="removeemployee", description="[Админ] Удалить сотрудника"),
        BotCommand(command="listemployees", description="[Админ] Список сотрудников"),
        BotCommand(command="cancel", description="Отменить текущее действие"),
    ])

    # Запуск планировщика напоминаний
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")

    # Действия при старте
    await on_startup()

    # Инициализация LLM-агента
    from app.agent.llm_agent import agent
    if agent.is_available():
        logger.info(f"LLM agent enabled with model: {settings.llm_model}")
    else:
        logger.info("LLM agent disabled (no API key configured)")

    try:
        # Запуск polling
        logger.info("Bot started polling")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown()
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
