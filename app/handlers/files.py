from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from urllib.parse import quote

from app.db.base import async_session_maker
from app.services.yadisk_service import YandexDiskService
from app.utils import escape_html

router = Router()


@router.message(Command("find"))
async def cmd_find_file(message: Message):
    """Поиск файла на Яндекс.Диске"""
    # Извлекаем запрос из команды
    query = message.text.replace("/find", "").strip()

    if not query:
        await message.answer(
            "🔍 <b>Поиск файлов на Яндекс.Диске</b>\n\n"
            "Использование: <code>/find название файла</code>\n"
            "Например: <code>/find сценарий Горизонт</code>",
            parse_mode="HTML"
        )
        return

    # Escape query for safe HTML output
    safe_query = escape_html(query)

    await message.answer(f"🔍 Ищу файлы по запросу: <b>{safe_query}</b>...", parse_mode="HTML")

    async with async_session_maker() as session:
        results = await YandexDiskService.search_files(session, query)

    if not results:
        await message.answer(
            f"📭 Файлы по запросу «{safe_query}» не найдены.\n\n"
            "Попробуйте изменить запрос или проверьте, что файлы есть на Яндекс.Диске."
        )
        return

    # Формируем ответ
    response = f"📁 <b>Найдено файлов: {len(results)}</b>\n\n"

    for file in results[:10]:  # Показываем максимум 10 результатов
        file_type_emoji = {
            "video": "🎬",
            "photo": "🖼",
            "document": "📄",
            "scenario": "📝",
        }.get(file.file_type, "📎")

        # Escape file data for safe HTML output
        safe_filename = escape_html(file.file_name)

        response += f"{file_type_emoji} <b>{safe_filename}</b>\n"

        # Получаем публичную ссылку (создаём если нет)
        async with async_session_maker() as session:
            public_url = await YandexDiskService.ensure_public_url(session, file)

        if public_url:
            safe_url = escape_html(public_url)
            response += f"🔗 <a href='{safe_url}'>Открыть файл</a>\n"
        else:
            # Если не удалось получить публичную ссылку - показываем путь
            safe_filepath = escape_html(file.file_path)
            response += f"📂 Путь: <code>{safe_filepath}</code>\n"

        response += "\n"

    if len(results) > 10:
        response += f"<i>... и ещё {len(results) - 10} файлов</i>"

    await message.answer(response, parse_mode="HTML", disable_web_page_preview=True)
