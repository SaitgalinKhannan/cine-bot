from datetime import datetime

from aiogram import Bot
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker
from app.services.event_service import EventService


class ReminderService:
    """Сервис для отправки напоминаний о событиях"""

    @staticmethod
    async def send_reminders(bot: Bot):
        """Проверить события и отправить напоминания"""
        logger.info("Checking events for reminders...")

        async with async_session_maker() as session:
            events_to_notify = await EventService.get_events_for_reminder(session)

            if not events_to_notify:
                logger.info("No events to notify")
                return

            logger.info(f"Found {len(events_to_notify)} events to notify")

            for event in events_to_notify:
                try:
                    await ReminderService._send_reminder(bot, session, event)
                except Exception as e:
                    logger.error(f"Error sending reminder for event {event.id}: {e}")

    @staticmethod
    async def _send_reminder(bot: Bot, session: AsyncSession, event):
        """Отправить напоминание о конкретном событии"""
        # Вычисляем количество дней до события
        days_until = (event.event_date - datetime.now()).days

        # Эмодзи для типов событий
        event_type_emoji = {
            "premiere": "🎬",
            "meeting": "📅",
            "birthday": "🎂",
            "other": "📌",
        }

        emoji = event_type_emoji.get(event.event_type, "📌")
        date_formatted = event.event_date.strftime("%d %B %Y в %H:%M")

        # Формируем текст напоминания
        if days_until == 0:
            time_text = "Сегодня"
        elif days_until == 1:
            time_text = "Завтра"
        else:
            time_text = f"Через {days_until} дн."

        message_text = (
            f"🔔 <b>Напоминание!</b>\n\n"
            f"{time_text}: {emoji} <b>{event.title}</b>\n"
            f"📅 {date_formatted}\n"
        )

        if event.description:
            message_text += f"\n📝 {event.description}"

        # Отправляем напоминание
        await bot.send_message(
            chat_id=event.chat_id,
            text=message_text,
            parse_mode="HTML"
        )

        # Отмечаем событие как уведомленное
        await EventService.mark_as_notified(session, event.id)

        logger.info(f"Reminder sent for event {event.id}: {event.title}")
