from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger

from app.config import settings
from app.db.base import async_session_maker
from app.services.user_service import UserService


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки авторизации пользователей"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """Проверить авторизацию перед обработкой сообщения"""

        # Пропускаем команду /start для всех
        if event.text and event.text.startswith("/start"):
            return await handler(event, data)

        user_id = event.from_user.id

        async with async_session_maker() as session:
            # Проверяем, авторизован ли пользователь
            is_authorized = await UserService.is_user_authorized(session, user_id)

            if not is_authorized:
                # Проверяем, является ли пользователь администратором по конфигу
                if user_id in settings.admin_ids_list:
                    # Автоматически создаем админа при первом обращении
                    await UserService.create_user(
                        session=session,
                        telegram_id=user_id,
                        username=event.from_user.username,
                        full_name=event.from_user.full_name,
                        role="admin",
                    )
                    logger.info(f"Auto-created admin user: {user_id}")
                    # Продолжаем обработку
                    return await handler(event, data)
                else:
                    # Неавторизованный пользователь
                    await event.answer(
                        "🚫 <b>Доступ запрещен</b>\n\n"
                        "Этот бот доступен только для сотрудников компании.\n"
                        "Обратитесь к администратору для получения доступа.",
                        parse_mode="HTML"
                    )
                    logger.warning(f"Unauthorized access attempt from user {user_id}")
                    return

            # Сохраняем информацию о пользователе в data для использования в хендлерах
            user = await UserService.get_user_by_telegram_id(session, user_id)
            data["user"] = user
            data["is_admin"] = user.role == "admin" if user else False

        return await handler(event, data)
