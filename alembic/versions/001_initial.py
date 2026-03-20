"""Initial migration: events and yandex_files_cache tables

Revision ID: 001_initial
Revises:
Create Date: 2026-03-16 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы events
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_date', sa.TIMESTAMP(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('remind_days', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('is_notified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Создание таблицы yandex_files_cache
    op.create_table(
        'yandex_files_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('file_name', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('public_url', sa.Text(), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Создание индексов для оптимизации запросов
    op.create_index('ix_events_event_date', 'events', ['event_date'])
    op.create_index('ix_events_is_notified', 'events', ['is_notified'])
    op.create_index('ix_yandex_files_file_name', 'yandex_files_cache', ['file_name'])


def downgrade() -> None:
    op.drop_index('ix_yandex_files_file_name', table_name='yandex_files_cache')
    op.drop_index('ix_events_is_notified', table_name='events')
    op.drop_index('ix_events_event_date', table_name='events')
    op.drop_table('yandex_files_cache')
    op.drop_table('events')
