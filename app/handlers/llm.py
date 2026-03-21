from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from app.agent.llm_agent import agent
from app.config import settings

router = Router()


@router.message(F.text & ~F.text.startswith('/'))
async def handle_natural_language(message: Message):
    """
    Обработчик обычных текстовых сообщений (не команд)
    Передаёт сообщение LLM-агенту для обработки только если есть триггерные слова
    """
    # Игнорируем сообщения от ботов
    if message.from_user.is_bot:
        return

    # Проверяем, доступен ли агент
    if not agent.is_available():
        logger.debug("LLM agent not available, ignoring message")
        return

    text_to_process = message.text.lower()

    # Получаем триггерные слова из конфига
    trigger_words = settings.trigger_words_list

    # Проверяем наличие триггерных слов
    has_trigger = any(word in text_to_process for word in trigger_words)

    if not has_trigger:
        logger.debug(f"No trigger words found in message: {message.text[:50]}...")
        return

    # В групповых чатах проверяем, что это наш целевой чат
    if message.chat.type in ["group", "supergroup"]:
        # Если указан GROUP_CHAT_ID, работаем только в этом чате
        if settings.group_chat_id and message.chat.id != settings.group_chat_id:
            logger.debug(f"Message from non-target group chat: {message.chat.id}")
            return

        logger.info(f"Processing group message with trigger word: {message.text[:50]}...")

    try:
        # Обрабатываем сообщение через LLM-агент
        response = await agent.process_message(
            message=message.text,  # Используем оригинальный текст
            chat_id=message.chat.id
        )

        # Проверяем, что ответ не пустой
        if not response or not response.strip():
            logger.warning("Agent returned empty response")
            response = "❌ Не удалось получить ответ. Попробуйте переформулировать запрос."

        # Отправляем ответ (ссылки на файлы будут без preview)
        await message.answer(response, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error in natural language handler: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке сообщения.\n"
            "Используйте /help для просмотра доступных команд."
        )
