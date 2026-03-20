.PHONY: help start stop restart logs status db shell migrate build clean check

help:
	@echo "🤖 CineBot - Makefile команды"
	@echo ""
	@echo "Использование: make [команда]"
	@echo ""
	@echo "Команды:"
	@echo "  start    - Запустить бота"
	@echo "  stop     - Остановить бота"
	@echo "  restart  - Перезапустить бота"
	@echo "  logs     - Показать логи"
	@echo "  status   - Статус сервисов"
	@echo "  db       - Подключиться к PostgreSQL"
	@echo "  shell    - Открыть shell в контейнере"
	@echo "  migrate  - Применить миграции БД"
	@echo "  build    - Пересобрать образы"
	@echo "  clean    - Удалить все данные"
	@echo "  check    - Проверить готовность проекта"

start:
	@echo "🚀 Запуск CineBot..."
	docker compose up -d
	@echo "✅ Бот запущен"

stop:
	@echo "🛑 Остановка CineBot..."
	docker compose down
	@echo "✅ Бот остановлен"

restart:
	@echo "🔄 Перезапуск CineBot..."
	docker compose restart bot
	@echo "✅ Бот перезапущен"

logs:
	@echo "📋 Логи бота (Ctrl+C для выхода):"
	docker compose logs -f bot

status:
	@echo "📊 Статус сервисов:"
	docker compose ps

db:
	@echo "🗄️  Подключение к базе данных..."
	docker compose exec db psql -U cinebot -d cinebot_db

shell:
	@echo "🐚 Подключение к контейнеру бота..."
	docker compose exec bot /bin/bash

migrate:
	@echo "🔄 Применение миграций..."
	docker compose exec bot alembic upgrade head
	@echo "✅ Миграции применены"

build:
	@echo "🔨 Пересборка образов..."
	docker compose build --no-cache
	@echo "✅ Образы пересобраны"

clean:
	@echo "🧹 Очистка (удаление контейнеров и volumes)..."
	docker compose down -v
	@echo "✅ Очистка завершена"

check:
	@echo "🔍 Проверка готовности проекта..."
	@bash check_setup.sh
