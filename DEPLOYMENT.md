# Руководство по развёртыванию CineBot

## Развёртывание на VPS

### Требования

- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Docker 20.10+
- Docker Compose 2.0+
- 1 GB RAM минимум (рекомендуется 2 GB)
- 10 GB свободного места на диске
- Открытый порт для SSH (22)

### Шаг 1: Подготовка сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Установить Docker Compose
sudo apt install docker-compose-plugin -y

# Проверить установку
docker --version
docker compose version
```

### Шаг 2: Клонирование проекта

```bash
# Создать директорию для проекта
mkdir -p ~/apps
cd ~/apps

# Клонировать репозиторий
git clone <repository-url> cinebot
cd cinebot

# Или загрузить через scp
# scp -r cinebot/ user@server:~/apps/
```

### Шаг 3: Настройка окружения

```bash
# Создать .env из шаблона
cp .env.example .env

# Отредактировать .env
nano .env
```

Заполнить реальными значениями:
```env
BOT_TOKEN=ваш_реальный_токен_от_BotFather
GROUP_CHAT_ID=-1001234567890
YANDEX_DISK_TOKEN=ваш_токен_яндекс_диска
```

### Шаг 4: Запуск

```bash
# Проверить готовность
./check_setup.sh

# Запустить в фоновом режиме
docker compose up -d

# Проверить статус
docker compose ps

# Посмотреть логи
docker compose logs -f bot
```

### Шаг 5: Проверка работы

```bash
# Проверить, что контейнеры запущены
docker compose ps

# Должно быть:
# cinebot-db-1   postgres:16-alpine   Up
# cinebot-bot-1  cinebot-bot          Up

# Проверить логи бота
docker compose logs bot | grep "Bot started polling"

# Если видите "Bot started polling" - всё работает!
```

### Шаг 6: Настройка автозапуска

```bash
# Создать systemd service
sudo nano /etc/systemd/system/cinebot.service
```

Содержимое файла:
```ini
[Unit]
Description=CineBot Telegram Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/YOUR_USER/apps/cinebot
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=YOUR_USER

[Install]
WantedBy=multi-user.target
```

Заменить `YOUR_USER` на ваше имя пользователя.

```bash
# Включить автозапуск
sudo systemctl enable cinebot.service

# Запустить сервис
sudo systemctl start cinebot.service

# Проверить статус
sudo systemctl status cinebot.service
```

## Обновление бота

### Обновление кода

```bash
cd ~/apps/cinebot

# Остановить бота
docker compose down

# Получить обновления
git pull origin main

# Пересобрать образ (если изменился код)
docker compose build --no-cache

# Запустить
docker compose up -d

# Проверить логи
docker compose logs -f bot
```

### Обновление зависимостей

```bash
# Если изменился requirements.txt
docker compose build --no-cache bot
docker compose up -d
```

### Применение миграций

```bash
# Применить новые миграции
docker compose exec bot alembic upgrade head

# Проверить текущую версию
docker compose exec bot alembic current
```

## Резервное копирование

### Backup базы данных

```bash
# Создать backup
docker compose exec db pg_dump -U cinebot cinebot_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Или с помощью скрипта
cat > backup.sh << 'SCRIPT'
#!/bin/bash
BACKUP_DIR="$HOME/backups/cinebot"
mkdir -p "$BACKUP_DIR"
FILENAME="cinebot_backup_$(date +%Y%m%d_%H%M%S).sql"
docker compose exec -T db pg_dump -U cinebot cinebot_db > "$BACKUP_DIR/$FILENAME"
gzip "$BACKUP_DIR/$FILENAME"
echo "Backup created: $BACKUP_DIR/$FILENAME.gz"
# Удалить старые backup'ы (старше 30 дней)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
SCRIPT

chmod +x backup.sh
```

### Автоматический backup

```bash
# Добавить в crontab
crontab -e

# Backup каждый день в 02:00
0 2 * * * cd ~/apps/cinebot && ./backup.sh
```

### Восстановление из backup

```bash
# Остановить бота
docker compose down

# Восстановить БД
gunzip -c backup_20260316_020000.sql.gz | docker compose exec -T db psql -U cinebot -d cinebot_db

# Запустить бота
docker compose up -d
```

## Мониторинг

### Логи

```bash
# Просмотр логов в реальном времени
docker compose logs -f bot

# Последние 100 строк
docker compose logs --tail=100 bot

# Логи за последний час
docker compose logs --since 1h bot

# Логи в файле
tail -f logs/bot.log
```

### Использование ресурсов

```bash
# Статистика контейнеров
docker stats

# Использование диска
docker system df

# Очистка неиспользуемых образов
docker system prune -a
```

### Проверка здоровья

```bash
# Статус контейнеров
docker compose ps

# Проверка БД
docker compose exec db psql -U cinebot -d cinebot_db -c "SELECT COUNT(*) FROM events;"

# Проверка бота через API
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

## Безопасность

### Firewall

```bash
# Установить ufw
sudo apt install ufw -y

# Разрешить SSH
sudo ufw allow 22/tcp

# Включить firewall
sudo ufw enable

# Проверить статус
sudo ufw status
```

### Обновления безопасности

```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Защита .env

```bash
# Ограничить права доступа
chmod 600 .env

# Проверить
ls -la .env
# Должно быть: -rw------- (только владелец может читать/писать)
```

## Масштабирование

### Увеличение ресурсов

Отредактировать `docker-compose.yml`:

```yaml
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Несколько инстансов

Для работы с несколькими группами можно запустить несколько инстансов:

```bash
# Создать копию проекта
cp -r cinebot cinebot-group2
cd cinebot-group2

# Изменить .env (другой GROUP_CHAT_ID)
nano .env

# Изменить порты в docker-compose.yml
# ports:
#   - "5433:5432"  # Другой порт для PostgreSQL

# Запустить
docker compose up -d
```

## Troubleshooting на продакшене

### Бот не запускается

```bash
# Проверить логи
docker compose logs bot

# Проверить .env
cat .env

# Проверить подключение к БД
docker compose exec db psql -U cinebot -d cinebot_db

# Пересоздать контейнеры
docker compose down -v
docker compose up -d
```

### Высокое использование памяти

```bash
# Проверить статистику
docker stats

# Ограничить память в docker-compose.yml
# mem_limit: 512m

# Перезапустить
docker compose restart bot
```

### База данных переполнена

```bash
# Очистить старые события
docker compose exec db psql -U cinebot -d cinebot_db
DELETE FROM events WHERE event_date < NOW() - INTERVAL '90 days';

# Очистить старый кэш файлов
DELETE FROM yandex_files_cache WHERE updated_at < NOW() - INTERVAL '30 days';

# Vacuum
VACUUM FULL;
```

## Мониторинг и алерты

### Простой мониторинг через cron

```bash
# Создать скрипт проверки
cat > check_bot.sh << 'SCRIPT'
#!/bin/bash
if ! docker compose ps | grep -q "Up"; then
    echo "CineBot is down!" | mail -s "CineBot Alert" admin@example.com
    docker compose up -d
fi
SCRIPT

chmod +x check_bot.sh

# Добавить в crontab (проверка каждые 5 минут)
*/5 * * * * cd ~/apps/cinebot && ./check_bot.sh
```

### Интеграция с Prometheus (опционально)

Для продвинутого мониторинга можно добавить экспортер метрик.

## Полезные команды

```bash
# Перезапуск бота
docker compose restart bot

# Просмотр логов БД
docker compose logs db

# Подключение к БД
docker compose exec db psql -U cinebot -d cinebot_db

# Backup БД
docker compose exec db pg_dump -U cinebot cinebot_db > backup.sql

# Очистка Docker
docker system prune -a --volumes

# Обновление и перезапуск
git pull && docker compose up -d --build

# Проверка версии
cat VERSION
```

## Контакты для поддержки

При возникновении проблем:
1. Проверьте [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Посмотрите логи: `docker compose logs bot`
3. Создайте issue в репозитории с описанием проблемы и логами
