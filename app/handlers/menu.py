from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.db.base import async_session_maker
from app.services.event_service import EventService
from app.services.yadisk_service import YandexDiskService
from app.services.user_service import UserService
from app.states.event_states import AddEventFSM, DeleteEventFSM
from app.utils import escape_html

router = Router()


def get_main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню с inline-кнопками"""
    buttons = [
        [
            InlineKeyboardButton(text="📅 События", callback_data="menu:events"),
            InlineKeyboardButton(text="📁 Файлы", callback_data="menu:files"),
        ],
        [
            InlineKeyboardButton(text="❓ Помощь", callback_data="menu:help"),
        ],
    ]

    # Добавляем админ-кнопку только для администраторов
    if is_admin:
        buttons.insert(1, [
            InlineKeyboardButton(text="👑 Админ", callback_data="menu:admin"),
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_events_menu() -> InlineKeyboardMarkup:
    """Меню управления событиями"""
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить событие", callback_data="events:add")],
        [InlineKeyboardButton(text="📋 Список событий", callback_data="events:list")],
        [InlineKeyboardButton(text="🗑 Удалить событие", callback_data="events:delete")],
        [InlineKeyboardButton(text="📅 Экспорт в календарь", callback_data="events:export")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_files_menu() -> InlineKeyboardMarkup:
    """Меню работы с файлами"""
    buttons = [
        [InlineKeyboardButton(text="🔍 Найти файл", callback_data="files:search")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_menu() -> InlineKeyboardMarkup:
    """Меню администратора"""
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить сотрудника", callback_data="admin:add_employee")],
        [InlineKeyboardButton(text="➖ Удалить сотрудника", callback_data="admin:remove_employee")],
        [InlineKeyboardButton(text="👥 Список сотрудников", callback_data="admin:list_employees")],
        [InlineKeyboardButton(text="🔄 Синхронизация файлов", callback_data="admin:sync_files")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("menu"))
async def cmd_menu(message: Message, is_admin: bool = False):
    """Показать главное меню"""
    await message.answer(
        "🤖 <b>Главное меню CineBot</b>\n\n"
        "Выберите раздел:",
        parse_mode="HTML",
        reply_markup=get_main_menu(is_admin)
    )


@router.callback_query(F.data == "menu:main")
async def callback_main_menu(callback: CallbackQuery, is_admin: bool = False):
    """Вернуться в главное меню"""
    await callback.message.edit_text(
        "🤖 <b>Главное меню CineBot</b>\n\n"
        "Выберите раздел:",
        parse_mode="HTML",
        reply_markup=get_main_menu(is_admin)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:events")
async def callback_events_menu(callback: CallbackQuery):
    """Меню событий"""
    await callback.message.edit_text(
        "📅 <b>Управление событиями</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_events_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:files")
async def callback_files_menu(callback: CallbackQuery):
    """Меню файлов"""
    await callback.message.edit_text(
        "📁 <b>Работа с файлами</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_files_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:admin")
async def callback_admin_menu(callback: CallbackQuery, is_admin: bool = False):
    """Меню администратора"""
    if not is_admin:
        await callback.answer("🚫 Доступно только администраторам", show_alert=True)
        return

    await callback.message.edit_text(
        "👑 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def callback_help(callback: CallbackQuery):
    """Показать справку"""
    help_text = (
        "❓ <b>Справка по CineBot</b>\n\n"

        "<b>📅 СОБЫТИЯ</b>\n"
        "• <b>Добавить событие</b> — создать новое событие (премьера, встреча, день рождения)\n"
        "• <b>Список событий</b> — показать ближайшие запланированные события\n"
        "• <b>Удалить событие</b> — удалить событие по ID\n"
        "• <b>Экспорт в календарь</b> — скачать .ics файл для импорта в Google/Apple/Outlook календарь\n\n"

        "<b>📁 ФАЙЛЫ</b>\n"
        "• <b>Найти файл</b> — поиск файлов на Яндекс.Диске по названию\n\n"

        "<b>👑 АДМИН</b> (только для администраторов)\n"
        "• <b>Добавить сотрудника</b> — добавить пользователя в список сотрудников\n"
        "• <b>Удалить сотрудника</b> — удалить пользователя из списка\n"
        "• <b>Список сотрудников</b> — показать всех сотрудников\n"
        "• <b>Синхронизация файлов</b> — принудительно обновить кэш файлов с Яндекс.Диска\n\n"

        "<b>🤖 LLM-АГЕНТ</b>\n"
        "Бот понимает естественный язык! Используйте триггерные слова:\n"
        "• <code>добавь/добавить</code> — добавить событие\n"
        "• <code>найди/найти</code> — найти файл\n"
        "• <code>покажи/покажите</code> — показать события\n"
        "• <code>удали/удалить</code> — удалить событие\n"
        "• <code>создай/создать</code> — создать событие\n"
        "• <code>запланируй/запланировать</code> — запланировать событие\n\n"

        "<b>Примеры:</b>\n"
        "• <i>Добавь премьеру фильма ФИЛЬМ 20 апреля в 19:00</i>\n"
        "• <i>Найди сценарий фильма Асия</i>\n"
        "• <i>Покажи ближайшие события</i>\n\n"

        "<b>📝 КОМАНДЫ</b>\n"
        "Все функции доступны через команды:\n"
        "/menu — главное меню\n"
        "/help — эта справка\n"
        "/addevent — добавить событие\n"
        "/events — список событий\n"
        "/find — найти файл\n"
        "/cancel — отменить текущее действие"
    )

    back_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")]
    ])

    await callback.message.edit_text(
        help_text,
        parse_mode="HTML",
        reply_markup=back_button
    )
    await callback.answer()


# ============================================
# СОБЫТИЯ - Callback handlers
# ============================================

@router.callback_query(F.data == "events:add")
async def callback_add_event(callback: CallbackQuery, state: FSMContext):
    """Начать добавление события через меню"""
    await state.set_state(AddEventFSM.waiting_for_title)
    await callback.message.answer(
        "📝 <b>Добавление нового события</b>\n\n"
        "Введите название события:\n"
        "(Например: Премьера фильма «ФИЛЬМ»)\n\n"
        "Для отмены используйте /cancel",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "events:list")
async def callback_list_events(callback: CallbackQuery):
    """Показать список событий через меню"""
    async with async_session_maker() as session:
        events = await EventService.get_upcoming_events(session, limit=10)

    if not events:
        await callback.message.answer("📭 Нет запланированных событий.")
        await callback.answer()
        return

    from app.handlers.events import EVENT_TYPE_EMOJI

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
            safe_title = escape_html(event.title)

            # Заголовок с эмодзи типа
            response += f"{emoji} <b>{safe_title}</b>\n"

            # Дата курсивом
            response += f"<i>{date_formatted}</i>"

            # ID и напоминание в одной строке
            response += f" • ID: {event.id}"
            if event.remind_days > 0:
                response += f" • Напоминание за {event.remind_days} дн."

            response += "\n\n"

    await callback.message.answer(response, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "events:delete")
async def callback_delete_event(callback: CallbackQuery, state: FSMContext):
    """Начать удаление события через меню"""
    async with async_session_maker() as session:
        events = await EventService.get_upcoming_events(session, limit=20)

    if not events:
        await callback.message.answer("📭 Нет событий для удаления.")
        await callback.answer()
        return

    from app.handlers.events import EVENT_TYPE_EMOJI

    # Формируем список событий
    response = "🗑 <b>Удаление события</b>\n\n"
    response += "Выберите событие для удаления (введите ID):\n\n"

    for event in events:
        emoji = EVENT_TYPE_EMOJI.get(event.event_type, "📌")
        date_formatted = event.event_date.strftime("%d.%m.%Y в %H:%M")
        safe_title = escape_html(event.title)
        response += f"🆔 <code>{event.id}</code> — {emoji} {safe_title} ({date_formatted})\n"

    response += "\nДля отмены используйте /cancel"

    await state.set_state(DeleteEventFSM.waiting_for_event_id)
    await callback.message.answer(response, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "events:export")
async def callback_export_calendar(callback: CallbackQuery):
    """Экспорт событий в календарь через меню"""
    from datetime import datetime
    from io import BytesIO
    from aiogram.types import BufferedInputFile
    from app.services.calendar_service import CalendarService
    from loguru import logger

    async with async_session_maker() as session:
        events = await EventService.get_upcoming_events(session, limit=100)

    if not events:
        await callback.message.answer("📭 Нет событий для экспорта.")
        await callback.answer()
        return

    status_msg = await callback.message.answer("📅 Генерирую календарь...")

    try:
        # Генерируем .ics файл
        ics_content = CalendarService.generate_ics(events)

        # Создаем файл
        file = BytesIO(ics_content)
        filename = f"events_{datetime.now().strftime('%Y-%m-%d')}.ics"

        # Отправляем файл
        document = BufferedInputFile(file.getvalue(), filename=filename)

        await callback.message.answer_document(
            document=document,
            caption=(
                f"📅 <b>Экспорт событий в календарь</b>\n\n"
                f"Экспортировано событий: {len(events)}\n\n"
                f"<b>Как импортировать:</b>\n"
                f"📱 Google Calendar: Настройки → Импорт\n"
                f"🍎 Apple Calendar: Файл → Импорт\n"
                f"📧 Outlook: Файл → Импорт/экспорт\n\n"
                f"Файл содержит все предстоящие события с напоминаниями."
            ),
            parse_mode="HTML"
        )

        # Удаляем статусное сообщение
        await status_msg.delete()
        await callback.answer()

    except Exception as e:
        logger.error(f"Error exporting calendar: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ Ошибка при экспорте календаря. Попробуйте позже."
        )
        await callback.answer()


# ============================================
# ФАЙЛЫ - Callback handlers
# ============================================

@router.callback_query(F.data == "files:search")
async def callback_search_files(callback: CallbackQuery):
    """Начать поиск файлов через меню"""
    await callback.message.answer(
        "🔍 <b>Поиск файлов на Яндекс.Диске</b>\n\n"
        "Введите название файла для поиска:\n"
        "(Например: сценарий ФИЛЬМ)\n\n"
        "Для отмены используйте /cancel",
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================
# АДМИН - Callback handlers
# ============================================

@router.callback_query(F.data == "admin:add_employee")
async def callback_add_employee(callback: CallbackQuery, is_admin: bool = False):
    """Инструкция по добавлению сотрудника"""
    if not is_admin:
        await callback.answer("🚫 Доступно только администраторам", show_alert=True)
        return

    await callback.message.answer(
        "➕ <b>Добавление сотрудника</b>\n\n"
        "<b>Как добавить:</b>\n"
        "1. Попросите пользователя написать любое сообщение в этот чат\n"
        "2. Ответьте на его сообщение командой /addemployee\n\n"
        "Или используйте: <code>/addemployee TELEGRAM_ID</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:remove_employee")
async def callback_remove_employee(callback: CallbackQuery, is_admin: bool = False):
    """Инструкция по удалению сотрудника"""
    if not is_admin:
        await callback.answer("🚫 Доступно только администраторам", show_alert=True)
        return

    await callback.message.answer(
        "➖ <b>Удаление сотрудника</b>\n\n"
        "<b>Как удалить:</b>\n"
        "1. Ответьте на сообщение пользователя командой /removeemployee\n\n"
        "Или используйте: <code>/removeemployee TELEGRAM_ID</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:list_employees")
async def callback_list_employees(callback: CallbackQuery, is_admin: bool = False):
    """Показать список сотрудников"""
    if not is_admin:
        await callback.answer("🚫 Доступно только администраторам", show_alert=True)
        return

    async with async_session_maker() as session:
        users = await UserService.get_all_users(session)

    if not users:
        await callback.message.answer("📭 Список сотрудников пуст.")
        await callback.answer()
        return

    # Группируем по ролям
    admins = [u for u in users if u.role == "admin"]
    employees = [u for u in users if u.role == "employee"]

    response = "👥 <b>Список сотрудников</b>\n\n"

    if admins:
        response += "👑 <b>Администраторы:</b>\n"
        for user in admins:
            status = "✅" if user.is_active else "❌"
            username = f"@{user.username}" if user.username else f"ID: {user.telegram_id}"
            response += f"{status} {user.full_name or 'Без имени'} ({username})\n"
        response += "\n"

    if employees:
        response += "👤 <b>Сотрудники:</b>\n"
        for user in employees:
            status = "✅" if user.is_active else "❌"
            username = f"@{user.username}" if user.username else f"ID: {user.telegram_id}"
            response += f"{status} {user.full_name or 'Без имени'} ({username})\n"

    response += f"\n<i>Всего: {len(users)} чел.</i>"

    await callback.message.answer(response, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:sync_files")
async def callback_sync_files(callback: CallbackQuery, is_admin: bool = False):
    """Синхронизация файлов с Яндекс.Диска"""
    from loguru import logger

    if not is_admin:
        await callback.answer("🚫 Доступно только администраторам", show_alert=True)
        return

    status_msg = await callback.message.answer("🔄 Начинаю синхронизацию файлов с Яндекс.Диска...")

    try:
        async with async_session_maker() as session:
            await YandexDiskService.sync_files_cache(session)

        await status_msg.edit_text(
            "✅ <b>Синхронизация завершена!</b>\n\n"
            "Кэш файлов обновлен. Теперь команда /find будет использовать актуальный список файлов.",
            parse_mode="HTML"
        )
        await callback.answer()
        logger.info(f"Admin {callback.from_user.id} triggered manual file sync via menu")

    except Exception as e:
        logger.error(f"Error in manual file sync: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ <b>Ошибка синхронизации</b>\n\n"
            "Не удалось обновить кэш файлов. Попробуйте позже.",
            parse_mode="HTML"
        )
        await callback.answer()

