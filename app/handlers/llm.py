from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from app.agent.llm_agent import agent

router = Router()


@router.message(F.text & ~F.text.startswith('/'))
async def handle_natural_language(message: Message):
    """
    Обработчик обычных текстовых сообщений (не команд)
    Передаёт сообщение LLM-агенту для обработки
    """
    # Игнорируем сообщения от ботов
    if message.from_user.is_bot:
        return

    # Проверяем, доступен ли агент
    if not agent.is_available():
        logger.debug("LLM agent not available, ignoring message")
        return

    # В групповых чатах с Privacy Mode обрабатываем упоминания бота
    text_to_process = message.text
    if message.chat.type in ["group", "supergroup"]:
        bot = message.bot
        bot_info = await bot.get_me()
        bot_username = f"@{bot_info.username}"

        # Если Privacy Mode включен и бота не упомянули - игнорируем
        if not bot_info.can_read_all_group_messages:
            if bot_username.lower() not in message.text.lower():
                logger.debug("Privacy Mode ON: message without bot mention, ignoring")
                return

            # Убираем упоминание бота из текста для обработки
            text_to_process = message.text.replace(bot_username, "").replace(bot_info.username, "").strip()
            logger.info(f"Privacy Mode ON: processing mention, text: {text_to_process[:50]}...")

    try:
        # Обрабатываем сообщение через LLM-агент
        response = await agent.process_message(
            message=text_to_process,
            chat_id=message.chat.id
        )

        # Отправляем ответ
        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in natural language handler: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке сообщения.\n"
            "Используйте /help для просмотра доступных команд."
        )
