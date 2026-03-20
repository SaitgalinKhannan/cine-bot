from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserService:
    """Сервис для работы с пользователями"""

    @staticmethod
    async def get_user_by_telegram_id(
        session: AsyncSession,
        telegram_id: int,
    ) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "employee",
    ) -> User:
        """Создать нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def is_user_authorized(
        session: AsyncSession,
        telegram_id: int,
    ) -> bool:
        """Проверить, авторизован ли пользователь"""
        user = await UserService.get_user_by_telegram_id(session, telegram_id)
        return user is not None and user.is_active

    @staticmethod
    async def is_admin(
        session: AsyncSession,
        telegram_id: int,
    ) -> bool:
        """Проверить, является ли пользователь администратором"""
        user = await UserService.get_user_by_telegram_id(session, telegram_id)
        return user is not None and user.role == "admin" and user.is_active

    @staticmethod
    async def get_all_users(
        session: AsyncSession,
    ) -> List[User]:
        """Получить всех пользователей"""
        query = select(User).order_by(User.created_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def deactivate_user(
        session: AsyncSession,
        telegram_id: int,
    ) -> bool:
        """Деактивировать пользователя"""
        user = await UserService.get_user_by_telegram_id(session, telegram_id)
        if user:
            user.is_active = False
            await session.commit()
            return True
        return False

    @staticmethod
    async def activate_user(
        session: AsyncSession,
        telegram_id: int,
    ) -> bool:
        """Активировать пользователя"""
        user = await UserService.get_user_by_telegram_id(session, telegram_id)
        if user:
            user.is_active = True
            await session.commit()
            return True
        return False
