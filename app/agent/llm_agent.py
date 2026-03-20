"""
LLM-агент для обработки команд на естественном языке
Использует OpenRouter API для парсинга намерений пользователя
"""

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger

from app.agent.tools import AGENT_TOOLS
from app.config import settings


class CineBotAgent:
    """LLM-агент для обработки естественного языка"""

    def __init__(self):
        """Инициализация агента"""
        self.llm = None
        self.chain = None
        self._initialize()

    def _initialize(self):
        """Инициализация LLM и агента"""
        if not settings.openrouter_api_key:
            logger.warning("OpenRouter API key not configured, LLM agent disabled")
            return

        try:
            # Инициализация LLM через OpenRouter
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.openrouter_api_key,
                base_url=settings.llm_base_url,
                temperature=0.1,
                max_tokens=2000,
            )

            # Системный промпт на русском языке
            system_prompt = """Ты — помощник для управления событиями кинокомпании и поиска файлов.

Твоя задача — понимать запросы пользователя на русском языке и вызывать соответствующие функции.

Доступные действия:
1. Добавить событие (премьера, встреча, день рождения)
2. Показать ближайшие события
3. Найти файл на Яндекс.Диске (два способа):
   - search_file: быстрый поиск по кэшу (для точных названий)
   - search_file_smart: умный поиск через API с анализом (для сложных запросов типа "файлы по фильму X")
4. Удалить событие по ID

Правила:
- Всегда отвечай на русском языке
- Будь кратким и по делу
- Если не уверен в намерении пользователя, уточни
- Для дат используй формат ДД.ММ.ГГГГ ЧЧ:ММ
- Типы событий: "premiere" (премьера), "meeting" (встреча), "birthday" (день рождения), "other" (другое)

Выбор инструмента поиска:
- Используй search_file_smart для запросов типа: "найди файлы по фильму X", "покажи все видео", "найди сценарии"
- Используй search_file для точных названий: "найди файл Горизонт_Сценарий.pdf"

Примеры запросов:
- "Добавь премьеру фильма Горизонт 20 апреля в 19:00"
- "Покажи ближайшие события"
- "Найди файлы по фильму Асия" → search_file_smart
- "Найди все сценарии" → search_file_smart
- "Найди Горизонт_Сценарий.pdf" → search_file
- "Удали событие 5"

Если пользователь просто здоровается или задаёт общий вопрос, отвечай дружелюбно, но напомни о доступных командах."""

            # Создание промпта
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
            ])

            # Привязка инструментов к LLM
            llm_with_tools = self.llm.bind_tools(AGENT_TOOLS)

            # Создание цепочки
            self.chain = prompt | llm_with_tools

            logger.info(f"LLM agent initialized with model: {settings.llm_model}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM agent: {e}")
            self.llm = None
            self.chain = None

    def is_available(self) -> bool:
        """Проверить, доступен ли агент"""
        return self.chain is not None

    async def process_message(self, message: str, chat_id: int) -> str:
        """
        Обработать сообщение пользователя

        Args:
            message: Текст сообщения
            chat_id: ID чата для контекста

        Returns:
            Ответ агента
        """
        if not self.is_available():
            return (
                "🤖 LLM-агент недоступен. Используйте команды:\n"
                "/addevent — добавить событие\n"
                "/events — показать события\n"
                "/find — найти файл\n"
                "/help — справка"
            )

        try:
            logger.info(f"Processing message with LLM: {message[:50]}...")

            # Вызов LLM с инструментами
            response = await self.chain.ainvoke({"input": message})

            # Проверяем, есть ли вызовы инструментов
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Выполняем первый вызов инструмента
                tool_call = response.tool_calls[0]
                tool_name = tool_call['name']
                tool_args = tool_call['args']

                logger.info(f"Tool call: {tool_name} with args: {tool_args}")

                # Находим и вызываем инструмент
                for tool in AGENT_TOOLS:
                    if tool.name == tool_name:
                        try:
                            result = await tool.ainvoke(tool_args)
                            logger.info(f"Tool result: {result[:100]}...")
                            return result
                        except Exception as e:
                            logger.error(f"Tool execution error: {e}")
                            return f"❌ Ошибка выполнения: {str(e)}"

                return "❌ Инструмент не найден"

            # Если нет вызовов инструментов, возвращаем текстовый ответ
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)

        except Exception as e:
            logger.error(f"Error processing message with LLM: {e}")
            return (
                "❌ Произошла ошибка при обработке запроса.\n\n"
                "Попробуйте использовать команды:\n"
                "/addevent — добавить событие\n"
                "/events — показать события\n"
                "/find — найти файл"
            )


# Глобальный экземпляр агента
agent = CineBotAgent()
