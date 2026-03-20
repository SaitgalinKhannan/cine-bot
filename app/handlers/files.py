from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db.base import async_session_maker
from app.services.yadisk_service import YandexDiskService

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

    await message.answer(f"🔍 Ищу файлы по запросу: <b>{query}</b>...", parse_mode="HTML")

    async with async_session_maker() as session:
        results = await YandexDiskService.search_files(session, query)

    if not results:
        await message.answer(
            f"📭 Файлы по запросу «{query}» не найдены.\n\n"
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

        response += f"{file_type_emoji} <b>{file.file_name}</b>\n"

        if file.public_url:
            response += f"🔗 <a href='{file.public_url}'>Открыть файл</a>\n"
        else:
            response += f"📂 Путь: <code>{file.file_path}</code>\n"

        response += "\n"

    if len(results) > 10:
        response += f"<i>... и ещё {len(results) - 10} файлов</i>"

    await message.answer(response, parse_mode="HTML", disable_web_page_preview=True)
