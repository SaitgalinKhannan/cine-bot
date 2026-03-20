from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Boolean, Text, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Event(Base):
    """Модель события (встречи, дни рождения, премьеры)"""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # meeting, birthday, premiere, other
    event_date: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    remind_days: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title='{self.title}', date={self.event_date})>"


class User(Base):
    """Модель пользователя (сотрудник или администратор)"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="employee", nullable=False)  # admin, employee
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role='{self.role}')>"


class YandexFileCache(Base):
    """Кэш файлов с Яндекс.Диска"""

    __tablename__ = "yandex_files_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    public_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # video, photo, document, scenario
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<YandexFileCache(id={self.id}, file_name='{self.file_name}')>"
