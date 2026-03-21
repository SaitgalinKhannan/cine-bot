from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.agent.tools import search_file
from app.utils import escape_html

router = Router()


@router.message(Command("find"))
async def cmd_find_file(message: Message):
    """Поиск файла на Яндекс.Диске (быстрый поиск по кэшу с умной сортировкой)"""
    # Извлекаем запрос из команды
    query = message.text.replace("/find", "").strip()

    if not query:
        await message.answer(
            "🔍 <b>Поиск файлов на Яндекс.Диске</b>\n\n"
            "Использование: <code>/find название файла</code>\n"
            "Например: <code>/find сценарий ФИЛЬМ</code>",
            parse_mode="HTML"
        )
        return

    # Escape query for safe HTML output
    safe_query = escape_html(query)

    await message.answer(f"🔍 Ищу файлы по запросу: <b>{safe_query}</b>...", parse_mode="HTML")

    result = await search_file.ainvoke({"query": query, "limit": 10})

    # Экранируем HTML-символы в ответе
    safe_result = escape_html(result)

    await message.answer(safe_result, parse_mode="HTML", disable_web_page_preview=True)
