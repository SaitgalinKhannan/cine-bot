from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from app.db.base import async_session_maker
from app.services.user_service import UserService

router = Router()


@router.message(Command("addemployee"))
async def cmd_add_employee(message: Message, is_admin: bool = False):
    """Добавить сотрудника (только для администраторов)"""
    if not is_admin:
        await message.answer("🚫 Эта команда доступна только администраторам.")
        return

    # Проверяем, есть ли reply на сообщение пользователя
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer(
            "❌ <b>Неверное использование команды</b>\n\n"
            "Чтобы добавить сотрудника:\n"
            "1. Попросите его написать любое сообщение в этот чат\n"
            "2. Ответьте на его сообщение командой /addemployee\n\n"
            "Или используйте: <code>/addemployee TELEGRAM_ID</code>",
            parse_mode="HTML"
        )
        return

    target_user = message.reply_to_message.from_user
    telegram_id = target_user.id

    async with async_session_maker() as session:
        # Проверяем, существует ли уже пользователь
        existing_user = await UserService.get_user_by_telegram_id(session, telegram_id)

        if existing_user:
            if existing_user.is_active:
                await message.answer(
                    f"ℹ️ Пользователь @{target_user.username or target_user.full_name} "
                    f"уже является сотрудником."
                )
            else:
                # Активируем деактивированного пользователя
                await UserService.activate_user(session, telegram_id)
                await message.answer(
                    f"✅ Пользователь @{target_user.username or target_user.full_name} "
                    f"снова активирован как сотрудник."
                )
            return

        # Создаем нового сотрудника
        user = await UserService.create_user(
            session=session,
            telegram_id=telegram_id,
            username=target_user.username,
            full_name=target_user.full_name,
            role="employee",
        )

        await message.answer(
            f"✅ <b>Сотрудник добавлен!</b>\n\n"
            f"👤 {target_user.full_name or 'Без имени'}\n"
            f"🆔 @{target_user.username or f'ID: {telegram_id}'}\n"
            f"📋 Роль: Сотрудник",
            parse_mode="HTML"
        )
        logger.info(f"Admin {message.from_user.id} added employee {telegram_id}")


@router.message(Command("removeemployee"))
async def cmd_remove_employee(message: Message, is_admin: bool = False):
    """Удалить сотрудника (только для администраторов)"""
    if not is_admin:
        await message.answer("🚫 Эта команда доступна только администраторам.")
        return

    # Проверяем, есть ли reply на сообщение пользователя
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer(
            "❌ <b>Неверное использование команды</b>\n\n"
            "Чтобы удалить сотрудника:\n"
            "1. Ответьте на его сообщение командой /removeemployee\n\n"
            "Или используйте: <code>/removeemployee TELEGRAM_ID</code>",
            parse_mode="HTML"
        )
        return

    target_user = message.reply_to_message.from_user
    telegram_id = target_user.id

    # Защита от удаления самого себя
    if telegram_id == message.from_user.id:
        await message.answer("❌ Вы не можете удалить сами себя.")
        return

    async with async_session_maker() as session:
        # Проверяем, существует ли пользователь
        existing_user = await UserService.get_user_by_telegram_id(session, telegram_id)

        if not existing_user:
            await message.answer(
                f"❌ Пользователь @{target_user.username or target_user.full_name} "
                f"не найден в списке сотрудников."
            )
            return

        # Защита от удаления администратора
        if existing_user.role == "admin":
            await message.answer("❌ Нельзя удалить администратора через эту команду.")
            return

        # Деактивируем пользователя
        await UserService.deactivate_user(session, telegram_id)

        await message.answer(
            f"✅ <b>Сотрудник удален</b>\n\n"
            f"👤 {target_user.full_name or 'Без имени'}\n"
            f"🆔 @{target_user.username or f'ID: {telegram_id}'}",
            parse_mode="HTML"
        )
        logger.info(f"Admin {message.from_user.id} removed employee {telegram_id}")


@router.message(Command("listemployees"))
async def cmd_list_employees(message: Message, is_admin: bool = False):
    """Показать список всех сотрудников (только для администраторов)"""
    if not is_admin:
        await message.answer("🚫 Эта команда доступна только администраторам.")
        return

    async with async_session_maker() as session:
        users = await UserService.get_all_users(session)

    if not users:
        await message.answer("📭 Список сотрудников пуст.")
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

    await message.answer(response, parse_mode="HTML")


@router.message(Command("syncfiles"))
async def cmd_sync_files(message: Message, is_admin: bool = False):
    """Принудительная синхронизация кэша файлов с Яндекс.Диска (только для администраторов)"""
    if not is_admin:
        await message.answer("🚫 Эта команда доступна только администраторам.")
        return

    status_msg = await message.answer("🔄 Начинаю синхронизацию файлов с Яндекс.Диска...")

    try:
        async with async_session_maker() as session:
            from app.services.yadisk_service import YandexDiskService
            await YandexDiskService.sync_files_cache(session)

        await status_msg.edit_text(
            "✅ <b>Синхронизация завершена!</b>\n\n"
            "Кэш файлов обновлен. Теперь команда /find будет использовать актуальный список файлов.",
            parse_mode="HTML"
        )
        logger.info(f"Admin {message.from_user.id} triggered manual file sync")

    except Exception as e:
        logger.error(f"Error in manual file sync: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ <b>Ошибка синхронизации</b>\n\n"
            "Не удалось обновить кэш файлов. Попробуйте позже.",
            parse_mode="HTML"
        )
