#!/bin/bash

# Быстрые команды для управления ботом

case "$1" in
    start)
        echo "🚀 Запуск CineBot..."
        docker compose up -d
        echo "✅ Бот запущен"
        echo "Просмотр логов: ./bot.sh logs"
        ;;
    stop)
        echo "🛑 Остановка CineBot..."
        docker compose down
        echo "✅ Бот остановлен"
        ;;
    restart)
        echo "🔄 Перезапуск CineBot..."
        docker compose restart bot
        echo "✅ Бот перезапущен"
        ;;
    logs)
        echo "📋 Логи бота (Ctrl+C для выхода):"
        docker compose logs -f bot
        ;;
    status)
        echo "📊 Статус сервисов:"
        docker compose ps
        ;;
    db)
        echo "🗄️  Подключение к базе данных..."
        docker compose exec db psql -U cinebot -d cinebot_db
        ;;
    shell)
        echo "🐚 Подключение к контейнеру бота..."
        docker compose exec bot /bin/bash
        ;;
    migrate)
        echo "🔄 Применение миграций..."
        docker compose exec bot alembic upgrade head
        echo "✅ Миграции применены"
        ;;
    build)
        echo "🔨 Пересборка образов..."
        docker compose build --no-cache
        echo "✅ Образы пересобраны"
        ;;
    clean)
        echo "🧹 Очистка (удаление контейнеров и volumes)..."
        read -p "Вы уверены? Все данные будут удалены! (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose down -v
            echo "✅ Очистка завершена"
        else
            echo "❌ Отменено"
        fi
        ;;
    *)
        echo "🤖 CineBot - Управление ботом"
        echo ""
        echo "Использование: ./bot.sh [команда]"
        echo ""
        echo "Команды:"
        echo "  start    - Запустить бота"
        echo "  stop     - Остановить бота"
        echo "  restart  - Перезапустить бота"
        echo "  logs     - Показать логи"
        echo "  status   - Статус сервисов"
        echo "  db       - Подключиться к PostgreSQL"
        echo "  shell    - Открыть shell в контейнере"
        echo "  migrate  - Применить миграции БД"
        echo "  build    - Пересобрать образы"
        echo "  clean    - Удалить все данные (осторожно!)"
        echo ""
        echo "Примеры:"
        echo "  ./bot.sh start"
        echo "  ./bot.sh logs"
        ;;
esac
