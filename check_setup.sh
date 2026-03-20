#!/bin/bash

# Скрипт для проверки готовности проекта к запуску

echo "🔍 Проверка структуры проекта CineBot..."
echo ""

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "   Скопируйте .env.example в .env и заполните реальными значениями:"
    echo "   cp .env.example .env"
    exit 1
else
    echo "✅ Файл .env найден"
fi

# Проверка наличия обязательных переменных в .env
required_vars=("BOT_TOKEN" "GROUP_CHAT_ID" "POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "DATABASE_URL" "YANDEX_DISK_TOKEN")

for var in "${required_vars[@]}"; do
    if grep -q "^${var}=" .env && ! grep -q "^${var}=your_" .env && ! grep -q "^${var}=.*xxxx" .env; then
        echo "✅ ${var} настроен"
    else
        echo "⚠️  ${var} требует настройки в .env"
    fi
done

echo ""
echo "🐳 Проверка Docker..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
else
    echo "✅ Docker установлен"
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
else
    echo "✅ Docker Compose установлен"
fi

echo ""
echo "📁 Проверка структуры файлов..."

required_files=(
    "app/main.py"
    "app/config.py"
    "app/scheduler.py"
    "app/db/base.py"
    "app/db/models.py"
    "app/handlers/common.py"
    "app/handlers/events.py"
    "app/handlers/files.py"
    "app/services/event_service.py"
    "app/services/reminder_service.py"
    "app/services/yadisk_service.py"
    "app/states/event_states.py"
    "alembic/env.py"
    "alembic/versions/001_initial.py"
    "docker-compose.yml"
    "Dockerfile"
    "requirements.txt"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file отсутствует"
        all_files_exist=false
    fi
done

echo ""
if [ "$all_files_exist" = true ]; then
    echo "✅ Все необходимые файлы на месте"
    echo ""
    echo "🚀 Проект готов к запуску!"
    echo ""
    echo "Следующие шаги:"
    echo "1. Убедитесь, что .env заполнен реальными значениями"
    echo "2. Запустите: docker compose up -d"
    echo "3. Проверьте логи: docker compose logs -f bot"
else
    echo "❌ Некоторые файлы отсутствуют"
    exit 1
fi
