from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event


class EventService:
    """Сервис для работы с событиями"""

    @staticmethod
    async def create_event(
        session: AsyncSession,
        title: str,
        event_type: str,
        event_date: datetime,
        chat_id: int,
        remind_days: int = 2,
        description: Optional[str] = None,
    ) -> Event:
        """Создать новое событие"""
        event = Event(
            title=title,
            event_type=event_type,
            event_date=event_date,
            chat_id=chat_id,
            remind_days=remind_days,
            description=description,
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    @staticmethod
    async def get_upcoming_events(
        session: AsyncSession,
        limit: int = 10,
    ) -> List[Event]:
        """Получить ближайшие события"""
        query = (
            select(Event)
            .where(Event.event_date >= datetime.now())
            .order_by(Event.event_date)
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_event_by_id(
        session: AsyncSession,
        event_id: int,
    ) -> Optional[Event]:
        """Получить событие по ID"""
        query = select(Event).where(Event.id == event_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_event(
        session: AsyncSession,
        event_id: int,
    ) -> bool:
        """Удалить событие"""
        query = delete(Event).where(Event.id == event_id)
        result = await session.execute(query)
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_events_for_reminder(
        session: AsyncSession,
    ) -> List[Event]:
        """Получить события, для которых нужно отправить напоминание"""
        now = datetime.now()

        query = select(Event).where(
            Event.is_notified == False,
            Event.event_date > now,
        )

        result = await session.execute(query)
        events = list(result.scalars().all())

        # Фильтруем события, для которых пришло время напоминания
        events_to_notify = []
        for event in events:
            days_until_event = (event.event_date - now).days
            if days_until_event <= event.remind_days:
                events_to_notify.append(event)

        return events_to_notify

    @staticmethod
    async def mark_as_notified(
        session: AsyncSession,
        event_id: int,
    ) -> None:
        """Отметить событие как уведомленное"""
        event = await EventService.get_event_by_id(session, event_id)
        if event:
            event.is_notified = True
            await session.commit()
