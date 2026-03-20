from datetime import datetime, timedelta
from icalendar import Calendar, Event as ICalEvent, Alarm
from typing import List

from app.db.models import Event


class CalendarService:
    """Сервис для работы с календарями"""

    @staticmethod
    def generate_ics(events: List[Event]) -> bytes:
        """
        Генерировать .ics файл из списка событий

        Args:
            events: Список событий для экспорта

        Returns:
            Содержимое .ics файла в байтах
        """
        cal = Calendar()
        cal.add('prodid', '-//CineBot Calendar//cinebot.local//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', 'CineBot События')
        cal.add('x-wr-timezone', 'Europe/Moscow')

        for event_model in events:
            event = ICalEvent()
            event.add('summary', event_model.title)
            event.add('dtstart', event_model.event_date)
            event.add('dtend', event_model.event_date)
            event.add('dtstamp', datetime.now())
            event.add('uid', f'cinebot-{event_model.id}@cinebot.local')

            # Добавляем тип события как категорию
            event_type_map = {
                'premiere': 'Премьера',
                'meeting': 'Встреча',
                'birthday': 'День рождения',
                'other': 'Другое'
            }
            category = event_type_map.get(event_model.event_type, event_model.event_type)
            event.add('categories', [category])

            # Добавляем напоминание
            if event_model.reminder_days and event_model.reminder_days > 0:
                alarm = Alarm()
                alarm.add('action', 'DISPLAY')
                alarm.add('description', f'Напоминание: {event_model.title}')
                alarm.add('trigger', timedelta(days=-event_model.reminder_days))
                event.add_component(alarm)

            cal.add_component(event)

        return cal.to_ical()

    @staticmethod
    def generate_google_calendar_link(event: Event) -> str:
        """
        Генерировать ссылку для добавления события в Google Calendar

        Args:
            event: Событие для экспорта

        Returns:
            URL для добавления в Google Calendar
        """
        from urllib.parse import urlencode

        base_url = "https://calendar.google.com/calendar/render"

        # Форматируем дату для Google Calendar (YYYYMMDDTHHMMSS)
        date_str = event.event_date.strftime('%Y%m%dT%H%M%S')

        event_type_map = {
            'premiere': 'Премьера',
            'meeting': 'Встреча',
            'birthday': 'День рождения',
            'other': 'Другое'
        }
        event_type_ru = event_type_map.get(event.event_type, event.event_type)

        params = {
            'action': 'TEMPLATE',
            'text': event.title,
            'dates': f'{date_str}/{date_str}',
            'details': f'Тип: {event_type_ru}',
            'ctz': 'Europe/Moscow'
        }

        return f"{base_url}?{urlencode(params)}"
