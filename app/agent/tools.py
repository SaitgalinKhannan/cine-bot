"""
Инструменты для LLM-агента
Эти функции вызываются агентом для выполнения действий
"""

from datetime import datetime
from typing import Optional

from langchain.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker
from app.services.event_service import EventService
from app.services.yadisk_service import YandexDiskService


@tool
async def add_event(
    title: str,
    date_str: str,
    event_type: str = "other",
    remind_days: int = 2,
    chat_id: int = 0,
    description: Optional[str] = None
) -> str:
    """
    Добавить новое событие в календарь.

    Args:
        title: Название события (например: "Премьера фильма ФИЛЬМ")
        date_str: Дата в формате ДД.ММ.ГГГГ ЧЧ:ММ (например: "20.04.2026 19:00")
        event_type: Тип события - "premiere", "meeting", "birthday" или "other"
        remind_days: За сколько дней напомнить (по умолчанию 2)
        chat_id: ID чата для напоминания
        description: Дополнительное описание (опционально)

    Returns:
        Сообщение об успешном добавлении или ошибке
    """
    try:
        # Парсинг даты
        event_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M")

        # Проверка, что дата в будущем
        if event_date <= datetime.now():
            return "❌ Ошибка: дата должна быть в будущем"

        # Валидация типа события
        valid_types = ["premiere", "meeting", "birthday", "other"]
        if event_type not in valid_types:
            event_type = "other"

        # Сохранение в БД
        async with async_session_maker() as session:
            event = await EventService.create_event(
                session=session,
                title=title,
                event_type=event_type,
                event_date=event_date,
                chat_id=chat_id,
                remind_days=remind_days,
                description=description
            )

        emoji_map = {
            "premiere": "🎬",
            "meeting": "📅",
            "birthday": "🎂",
            "other": "📌"
        }
        emoji = emoji_map.get(event_type, "📌")

        return (
            f"✅ Событие добавлено!\n"
            f"{emoji} {event.title}\n"
            f"📅 {event.event_date.strftime('%d.%m.%Y в %H:%M')}\n"
            f"⏰ Напоминание за {remind_days} дн."
        )

    except ValueError as e:
        return f"❌ Ошибка формата даты. Используйте формат: ДД.ММ.ГГГГ ЧЧ:ММ (например: 20.04.2026 19:00)"
    except Exception as e:
        return f"❌ Ошибка при добавлении события: {str(e)}"


@tool
async def list_events(limit: int = 10) -> str:
    """
    Показать ближайшие события.

    Args:
        limit: Максимальное количество событий (по умолчанию 10)

    Returns:
        Список ближайших событий или сообщение, что событий нет
    """
    try:
        async with async_session_maker() as session:
            events = await EventService.get_upcoming_events(session, limit=limit)

        if not events:
            return "📭 Нет запланированных событий"

        emoji_map = {
            "premiere": "🎬",
            "meeting": "📅",
            "birthday": "🎂",
            "other": "📌"
        }

        result = f"📅 Ближайшие события ({len(events)}):\n\n"

        for event in events:
            emoji = emoji_map.get(event.event_type, "📌")
            date_str = event.event_date.strftime("%d.%m.%Y в %H:%M")
            result += f"{emoji} {event.title}\n"
            result += f"📅 {date_str}\n"
            if event.remind_days > 0:
                result += f"⏰ Напоминание за {event.remind_days} дн.\n"
            result += f"🆔 ID: {event.id}\n\n"

        return result

    except Exception as e:
        return f"❌ Ошибка при получении событий: {str(e)}"


@tool
async def search_file(query: str, limit: int = 5) -> str:
    """
    Найти файл на Яндекс.Диске (поиск по кэшу).

    Args:
        query: Поисковый запрос (название файла или его часть)
        limit: Максимальное количество результатов (по умолчанию 5)

    Returns:
        Список найденных файлов со ссылками или сообщение, что файлы не найдены
    """
    try:
        async with async_session_maker() as session:
            files = await YandexDiskService.search_files(session, query, limit=limit)

        if not files:
            return f"📭 Файлы по запросу «{query}» не найдены"

        emoji_map = {
            "video": "🎬",
            "photo": "🖼",
            "document": "📄",
            "scenario": "📝"
        }

        result = f"📁 Найдено файлов: {len(files)}\n\n"

        for file in files:
            emoji = emoji_map.get(file.file_type, "📎")
            result += f"{emoji} {file.file_name}\n"
            if file.public_url:
                result += f"🔗 {file.public_url}\n"
            else:
                result += f"📂 {file.file_path}\n"
            result += "\n"

        return result

    except Exception as e:
        return f"❌ Ошибка при поиске файлов: {str(e)}"


@tool
async def search_file_smart(query: str, limit: int = 10) -> str:
    """
    Умный поиск файлов на Яндекс.Диске через LLM.
    Получает актуальный список файлов через API и использует LLM для отбора релевантных.

    Args:
        query: Поисковый запрос (например: "файлы по фильму Асия", "все сценарии")
        limit: Максимальное количество результатов (по умолчанию 10)

    Returns:
        Список найденных файлов со ссылками или сообщение, что файлы не найдены
    """
    try:
        from langchain_openai import ChatOpenAI
        from app.config import settings

        # Получаем актуальный список файлов через API
        all_files = await YandexDiskService.get_files_realtime()

        if not all_files:
            return "📭 На Яндекс.Диске не найдено файлов"

        # Предварительная фильтрация: ищем файлы, содержащие хотя бы одно слово из запроса
        query_words = query.lower().split()
        filtered_files = []

        for file in all_files:
            file_name_lower = file['name'].lower()
            # Если хотя бы одно слово из запроса есть в названии файла
            if any(word in file_name_lower for word in query_words):
                filtered_files.append(file)

        # Если после фильтрации ничего не найдено, возвращаем пустой результат
        if not filtered_files:
            return f"📭 Файлы по запросу «{query}» не найдены"

        # Ограничиваем до 500 файлов для отправки в LLM (берем отфильтрованные)
        files_for_llm = filtered_files[:500]

        # Формируем список названий файлов для LLM
        file_names = [f"{i+1}. {file['name']}" for i, file in enumerate(files_for_llm)]
        files_text = "\n".join(file_names)

        # Создаем промпт для LLM
        llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.llm_base_url,
            temperature=0.1,
        )

        prompt = f"""Пользователь ищет: "{query}"

Список файлов на Яндекс.Диске:
{files_text}

Задача: Выбери наиболее релевантные файлы (максимум {limit} штук).
Верни ТОЛЬКО номера файлов через запятую (например: 1,5,12,23).
Если подходящих файлов нет, верни "НЕТ"."""

        response = await llm.ainvoke(prompt)
        selected = response.content.strip()

        if selected == "НЕТ" or not selected:
            return f"📭 Файлы по запросу «{query}» не найдены"

        # Парсим номера выбранных файлов
        try:
            indices = [int(num.strip()) - 1 for num in selected.split(",") if num.strip().isdigit()]
        except:
            return f"📭 Файлы по запросу «{query}» не найдены"

        # Формируем результат
        emoji_map = {
            "video": "🎬",
            "photo": "🖼",
            "document": "📄",
            "scenario": "📝"
        }

        result = f"📁 Найдено файлов: {len(indices)}\n\n"

        for idx in indices[:limit]:
            if 0 <= idx < len(files_for_llm):
                file = files_for_llm[idx]
                emoji = emoji_map.get(file['type'], "📎")
                result += f"{emoji} {file['name']}\n"

                # Если нет публичной ссылки - создаем её
                if not file.get('public_url'):
                    public_url = YandexDiskService.publish_file(file['path'])
                    if public_url:
                        file['public_url'] = public_url

                # Показываем ссылку
                if file.get('public_url'):
                    result += f"🔗 {file['public_url']}\n"
                else:
                    result += f"📂 {file['path']}\n"
                result += "\n"

        return result

    except Exception as e:
        return f"❌ Ошибка при умном поиске файлов: {str(e)}"


@tool
async def delete_event(event_id: int) -> str:
    """
    Удалить событие по ID.

    Args:
        event_id: ID события для удаления

    Returns:
        Сообщение об успешном удалении или ошибке
    """
    try:
        async with async_session_maker() as session:
            # Проверяем существование события
            event = await EventService.get_event_by_id(session, event_id)

            if not event:
                return f"❌ Событие с ID {event_id} не найдено"

            title = event.title

            # Удаляем
            success = await EventService.delete_event(session, event_id)

            if success:
                return f"✅ Событие «{title}» удалено"
            else:
                return f"❌ Не удалось удалить событие"

    except Exception as e:
        return f"❌ Ошибка при удалении события: {str(e)}"


# Список всех инструментов для агента
AGENT_TOOLS = [
    add_event,
    list_events,
    search_file,
    search_file_smart,
    delete_event,
]
