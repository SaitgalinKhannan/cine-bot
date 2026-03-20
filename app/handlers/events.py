from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker
from app.services.event_service import EventService
from app.states.event_states import AddEventFSM, DeleteEventFSM

router = Router()

# Типы событий с эмодзи
EVENT_TYPES = {
    "🎬 Премьера": "premiere",
    "📅 Встреча": "meeting",
    "🎂 День рождения": "birthday",
    "📌 Другое": "other",
}

EVENT_TYPE_EMOJI = {
    "premiere": "🎬",
    "meeting": "📅",
    "birthday": "🎂",
    "other": "📌",
}


@router.message(Command("addevent"))
async def cmd_add_event(message: Message, state: FSMContext):
    """Начало добавления события"""
    # Проверяем, групповой ли это чат
    if message.chat.type in ["group", "supergroup"]:
        # Получаем информацию о боте
        bot = message.bot
        bot_info = await bot.get_me()

        if not bot_info.can_read_all_group_messages:
            # Privacy Mode включен - FSM не будет работать в группе
            await message.answer(
                "⚠️ <b>FSM диалоги не работают в групповых чатах</b>\n\n"
                "У бота включен Privacy Mode, поэтому он не получает обычные сообщения в группе.\n\n"
                "<b>Варианты решения:</b>\n"
                "1️⃣ Напишите боту в личные сообщения для добавления события\n"
                "2️⃣ Используйте естественный язык с упоминанием бота:\n"
                f"   <code>@{bot_info.username} добавь премьеру фильма Горизонт 20 апреля в 19:00</code>\n"
                "3️⃣ Попросите администратора отключить Privacy Mode в @BotFather\n\n"
                "📚 Подробнее: см. документацию PRIVACY_MODE_FIX.md",
                parse_mode="HTML"
            )
            return

    await state.set_state(AddEventFSM.waiting_for_title)
    await message.answer(
        "📝 <b>Добавление нового события</b>\n\n"
        "Введите название события:\n"
        "(Например: Премьера фильма «Горизонт»)\n\n"
        "Для отмены используйте /cancel",
        parse_mode="HTML"
    )


@router.message(AddEventFSM.waiting_for_title)
async def process_event_title(message: Message, state: FSMContext):
    """Обработка названия события"""
    title = message.text.strip()

    if len(title) < 3:
        await message.answer("❌ Название слишком короткое. Введите минимум 3 символа:")
        return

    await state.update_data(title=title)
    await state.set_state(AddEventFSM.waiting_for_date)
    await message.answer(
        "📅 <b>Дата и время события</b>\n\n"
        "Введите дату в формате: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
        "Например: <code>20.04.2026 19:00</code>",
        parse_mode="HTML"
    )


@router.message(AddEventFSM.waiting_for_date)
async def process_event_date(message: Message, state: FSMContext):
    """Обработка даты события"""
    date_str = message.text.strip()

    try:
        event_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M")

        # Проверка, что дата в будущем
        if event_date <= datetime.now():
            await message.answer("❌ Дата должна быть в будущем. Попробуйте снова:")
            return

        await state.update_data(event_date=event_date)
        await state.set_state(AddEventFSM.waiting_for_type)

        # Клавиатура с типами событий
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🎬 Премьера"), KeyboardButton(text="📅 Встреча")],
                [KeyboardButton(text="🎂 День рождения"), KeyboardButton(text="📌 Другое")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await message.answer(
            "🎯 <b>Тип события</b>\n\n"
            "Выберите тип события:",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты!\n\n"
            "Используйте формат: <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
            "Например: <code>20.04.2026 19:00</code>",
            parse_mode="HTML"
        )


@router.message(AddEventFSM.waiting_for_type)
async def process_event_type(message: Message, state: FSMContext):
    """Обработка типа события"""
    event_type_text = message.text.strip()

    if event_type_text not in EVENT_TYPES:
        await message.answer(
            "❌ Пожалуйста, выберите тип события из предложенных кнопок:",
        )
        return

    event_type = EVENT_TYPES[event_type_text]
    await state.update_data(event_type=event_type)
    await state.set_state(AddEventFSM.waiting_for_remind_days)

    await message.answer(
        "⏰ <b>Напоминание</b>\n\n"
        "За сколько дней до события отправить напоминание?\n"
        "Введите число (например: 2) или 0, если напоминание не нужно:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AddEventFSM.waiting_for_remind_days)
async def process_remind_days(message: Message, state: FSMContext):
    """Обработка количества дней для напоминания"""
    try:
        remind_days = int(message.text.strip())

        if remind_days < 0:
            await message.answer("❌ Число не может быть отрицательным. Попробуйте снова:")
            return

        if remind_days > 365:
            await message.answer("❌ Слишком большое число. Максимум 365 дней:")
            return

        # Получаем все данные из состояния
        data = await state.get_data()

        # Сохраняем событие в БД
        async with async_session_maker() as session:
            event = await EventService.create_event(
                session=session,
                title=data["title"],
                event_type=data["event_type"],
                event_date=data["event_date"],
                chat_id=message.chat.id,
                remind_days=remind_days,
            )

        # Формируем подтверждение
        emoji = EVENT_TYPE_EMOJI.get(event.event_type, "📌")
        date_formatted = event.event_date.strftime("%d.%m.%Y в %H:%M")

        confirmation = (
            f"✅ <b>Событие добавлено!</b>\n\n"
            f"{emoji} <b>{event.title}</b>\n"
            f"📅 {date_formatted}\n"
        )

        if remind_days > 0:
            confirmation += f"⏰ Напоминание за {remind_days} дн.\n"
        else:
            confirmation += "⏰ Без напоминания\n"

        await message.answer(confirmation, parse_mode="HTML")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите целое число:")


@router.message(Command("events"))
async def cmd_list_events(message: Message):
    """Показать ближайшие события"""
    async with async_session_maker() as session:
        events = await EventService.get_upcoming_events(session, limit=10)

    if not events:
        await message.answer("📭 Нет запланированных событий.")
        return

    # Группируем события по типам
    events_by_type = {}
    for event in events:
        if event.event_type not in events_by_type:
            events_by_type[event.event_type] = []
        events_by_type[event.event_type].append(event)

    # Формируем сообщение
    response = "📅 <b>Ближайшие события:</b>\n\n"

    for event_type, type_events in events_by_type.items():
        emoji = EVENT_TYPE_EMOJI.get(event_type, "📌")

        for event in type_events:
            date_formatted = event.event_date.strftime("%d.%m.%Y в %H:%M")
            response += f"{emoji} <b>{event.title}</b>\n"
            response += f"📅 {date_formatted}\n"

            if event.remind_days > 0:
                response += f"⏰ Напоминание за {event.remind_days} дн.\n"

            response += f"🆔 ID: {event.id}\n\n"

    await message.answer(response, parse_mode="HTML")


@router.message(Command("delevent"))
async def cmd_delete_event(message: Message, state: FSMContext):
    """Начало удаления события"""
    async with async_session_maker() as session:
        events = await EventService.get_upcoming_events(session, limit=20)

    if not events:
        await message.answer("📭 Нет событий для удаления.")
        return

    # Формируем список событий
    response = "🗑 <b>Удаление события</b>\n\n"
    response += "Выберите событие для удаления (введите ID):\n\n"

    for event in events:
        emoji = EVENT_TYPE_EMOJI.get(event.event_type, "📌")
        date_formatted = event.event_date.strftime("%d.%m.%Y в %H:%M")
        response += f"🆔 <code>{event.id}</code> — {emoji} {event.title} ({date_formatted})\n"

    response += "\nДля отмены используйте /cancel"

    await state.set_state(DeleteEventFSM.waiting_for_event_id)
    await message.answer(response, parse_mode="HTML")


@router.message(DeleteEventFSM.waiting_for_event_id)
async def process_delete_event(message: Message, state: FSMContext):
    """Обработка удаления события"""
    try:
        event_id = int(message.text.strip())

        async with async_session_maker() as session:
            # Проверяем существование события
            event = await EventService.get_event_by_id(session, event_id)

            if not event:
                await message.answer("❌ Событие с таким ID не найдено. Попробуйте снова:")
                return

            # Удаляем событие
            await EventService.delete_event(session, event_id)

        await message.answer(f"✅ Событие «{event.title}» удалено.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите корректный ID события (число):")
