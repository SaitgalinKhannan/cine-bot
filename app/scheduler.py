from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from loguru import logger

from app.services.reminder_service import ReminderService
from app.services.yadisk_service import YandexDiskService
from app.db.base import async_session_maker


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Настройка планировщика задач"""
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    # Задача: проверка напоминаний каждый день в 09:00
    scheduler.add_job(
        ReminderService.send_reminders,
        trigger=CronTrigger(hour=9, minute=0),
        args=[bot],
        id="send_reminders",
        name="Send event reminders",
        replace_existing=True,
    )

    # Задача: синхронизация кэша Яндекс.Диска каждый день в 03:00
    async def sync_yadisk_job():
        """Job для синхронизации Яндекс.Диска"""
        try:
            async with async_session_maker() as session:
                await YandexDiskService.sync_files_cache(session)
        except Exception as e:
            logger.error(f"Error in Yandex.Disk sync job: {e}")

    scheduler.add_job(
        sync_yadisk_job,
        trigger=CronTrigger(hour=3, minute=0),
        id="sync_yadisk",
        name="Sync Yandex.Disk cache",
        replace_existing=True,
    )

    logger.info("Scheduler configured with jobs:")
    logger.info("  - send_reminders: daily at 09:00")
    logger.info("  - sync_yadisk: daily at 03:00")

    return scheduler
