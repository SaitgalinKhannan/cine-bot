from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "👋 Привет! Я CineBot — помощник для управления событиями кинокомпании.\n\n"
        "Используй /help для просмотра доступных команд."
    )


@router.message(Command("help"))
async def cmd_help(message: Message, is_admin: bool = False):
    """Обработчик команды /help"""
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/addevent — Добавить новое событие (премьера, встреча, день рождения)\n"
        "/events — Показать ближайшие события\n"
        "/delevent — Удалить событие\n"
        "/find &lt;запрос&gt; — Найти файл на Яндекс.Диске\n"
        "/cancel — Отменить текущее действие\n"
        "/help — Показать эту справку\n\n"
    )

    if is_admin:
        help_text += (
            "👑 <b>Команды администратора:</b>\n\n"
            "/addemployee — Добавить сотрудника (ответьте на его сообщение)\n"
            "/removeemployee — Удалить сотрудника (ответьте на его сообщение)\n"
            "/listemployees — Показать список всех сотрудников\n\n"
        )

    help_text += (
        "💡 <b>Примеры использования:</b>\n"
        "• /addevent — запустит пошаговый диалог добавления события\n"
        "• /find сценарий Горизонт — найдёт файлы со словами 'сценарий' и 'Горизонт'\n"
        "• /events — покажет ближайшие 10 событий\n\n"
        "🤖 <b>Естественный язык:</b>\n"
        "Можно общаться без команд! Просто напишите:\n"
        "• \"Добавь премьеру фильма Горизонт 20 апреля в 19:00\"\n"
        "• \"Покажи ближайшие события\"\n"
        "• \"Найди сценарий Горизонт\"\n"
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    """Обработчик команды /cancel - отмена текущего действия"""
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("Нечего отменять. Вы не в процессе выполнения команды.")
        return

    await state.clear()
    await message.answer(
        "✅ Действие отменено. Используй /help для просмотра команд.",
        reply_markup=None
    )
