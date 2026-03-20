# Troubleshooting Guide

## Проблемы при запуске

### Ошибка: "Cannot connect to the Docker daemon"

**Проблема:** Docker не запущен или у пользователя нет прав.

**Решение:**
```bash
# Запустить Docker
sudo systemctl start docker

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

### Ошибка: "port is already allocated"

**Проблема:** Порт 5432 уже занят другим процессом.

**Решение:**
```bash
# Найти процесс на порту 5432
sudo lsof -i :5432

# Остановить PostgreSQL, если он запущен локально
sudo systemctl stop postgresql

# Или изменить порт в docker-compose.yml
ports:
  - "5433:5432"  # Использовать другой внешний порт
```

### Ошибка: "validation error for Settings"

**Проблема:** Неправильно заполнен файл `.env`.

**Решение:**
```bash
# Проверить формат .env
cat .env

# Убедиться, что:
# - BOT_TOKEN начинается с цифр и содержит :
# - GROUP_CHAT_ID это число (например: -1001234567890)
# - Нет пробелов вокруг =
# - Нет кавычек вокруг значений
```

Правильный формат:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
GROUP_CHAT_ID=-1001234567890
```

Неправильный формат:
```env
BOT_TOKEN = "1234567890:ABC"  # ❌ Пробелы и кавычки
GROUP_CHAT_ID=-100xxxxxxxxxx  # ❌ Не число
```

## Проблемы с ботом

### Бот не отвечает на команды

**Диагностика:**
```bash
# Проверить статус контейнеров
docker compose ps

# Проверить логи бота
docker compose logs bot

# Проверить логи PostgreSQL
docker compose logs db
```

**Возможные причины:**

1. **Неверный токен бота**
   ```bash
   # Проверить токен
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

2. **Бот не добавлен в группу**
   - Добавьте бота в группу через Telegram
   - Дайте боту права администратора (если требуется)

3. **Неверный GROUP_CHAT_ID**
   ```bash
   # Получить правильный ID
   # 1. Напишите что-то в группе
   # 2. Откройте в браузере:
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   # 3. Найдите "chat":{"id":-1001234567890}
   ```

### Ошибка: "Database connection failed"

**Проблема:** Бот не может подключиться к PostgreSQL.

**Решение:**
```bash
# Проверить, что БД запущена
docker compose ps db

# Проверить логи БД
docker compose logs db

# Перезапустить БД
docker compose restart db

# Проверить подключение вручную
docker compose exec db psql -U cinebot -d cinebot_db
```

### Миграции не применяются

**Проблема:** Таблицы не создаются в БД.

**Решение:**
```bash
# Применить миграции вручную
docker compose exec bot alembic upgrade head

# Проверить текущую версию
docker compose exec bot alembic current

# Если ошибка, пересоздать БД
docker compose down -v
docker compose up -d
```

## Проблемы с Яндекс.Диском

### Ошибка: "Invalid Yandex.Disk token"

**Проблема:** Неверный или истекший токен.

**Решение:**
1. Получить новый токен на [OAuth Яндекса](https://oauth.yandex.ru/)
2. Обновить `YANDEX_DISK_TOKEN` в `.env`
3. Перезапустить бота: `docker compose restart bot`

### Файлы не находятся при поиске

**Проблема:** Кэш не синхронизирован.

**Решение:**
```bash
# Проверить логи синхронизации
docker compose logs bot | grep "Yandex.Disk"

# Синхронизация запускается автоматически в 03:00
# Для ручной синхронизации можно добавить команду (TODO)

# Временное решение: перезапустить бота
docker compose restart bot
```

### Ошибка: "Connection timeout" при синхронизации

**Проблема:** Медленное соединение или большое количество файлов.

**Решение:**
- Увеличить timeout в `yadisk_service.py`
- Синхронизировать только определенные папки
- Использовать более быстрое интернет-соединение

## Проблемы с напоминаниями

### Напоминания не приходят

**Диагностика:**
```bash
# Проверить, что планировщик запущен
docker compose logs bot | grep "Scheduler"

# Проверить задачи
docker compose logs bot | grep "send_reminders"
```

**Возможные причины:**

1. **Неверный часовой пояс**
   - Проверить timezone в `scheduler.py`
   - По умолчанию: `Europe/Moscow`

2. **События уже уведомлены**
   - Проверить флаг `is_notified` в БД
   ```bash
   docker compose exec db psql -U cinebot -d cinebot_db
   SELECT id, title, is_notified FROM events;
   ```

3. **Дата события в прошлом**
   - Напоминания отправляются только для будущих событий

## Проблемы с производительностью

### Бот медленно отвечает

**Решение:**
```bash
# Проверить использование ресурсов
docker stats

# Увеличить ресурсы для контейнеров в docker-compose.yml
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

### База данных переполнена

**Решение:**
```bash
# Очистить старые события
docker compose exec db psql -U cinebot -d cinebot_db
DELETE FROM events WHERE event_date < NOW() - INTERVAL '30 days';

# Очистить кэш файлов
DELETE FROM yandex_files_cache WHERE updated_at < NOW() - INTERVAL '7 days';
```

## Логи и отладка

### Просмотр логов

```bash
# Все логи
docker compose logs

# Только бот
docker compose logs bot

# Только БД
docker compose logs db

# Следить за логами в реальном времени
docker compose logs -f bot

# Последние 100 строк
docker compose logs --tail=100 bot
```

### Уровни логирования

Логи сохраняются в `logs/bot.log` с ротацией:
- Максимальный размер: 10 MB
- Хранение: 7 дней
- Уровень: INFO

Для отладки можно изменить уровень в `app/main.py`:
```python
logger.add(
    "logs/bot.log",
    level="DEBUG",  # Изменить на DEBUG
    ...
)
```

### Подключение к контейнеру

```bash
# Shell в контейнере бота
docker compose exec bot /bin/bash

# Shell в контейнере БД
docker compose exec db /bin/bash

# Python REPL в контейнере бота
docker compose exec bot python
```

## Полная переустановка

Если ничего не помогает:

```bash
# 1. Остановить и удалить все
docker compose down -v

# 2. Удалить образы
docker compose rm -f
docker rmi cine-bot-bot

# 3. Очистить логи
rm -rf logs/*

# 4. Пересобрать
docker compose build --no-cache

# 5. Запустить заново
docker compose up -d

# 6. Проверить логи
docker compose logs -f bot
```

## Получение помощи

Если проблема не решена:

1. Соберите информацию:
   ```bash
   docker compose ps > debug_info.txt
   docker compose logs >> debug_info.txt
   cat .env >> debug_info.txt  # Удалите токены перед отправкой!
   ```

2. Проверьте:
   - Версию Docker: `docker --version`
   - Версию Docker Compose: `docker compose version`
   - Версию Python в контейнере: `docker compose exec bot python --version`

3. Опишите проблему с деталями:
   - Что вы пытались сделать
   - Что произошло
   - Сообщения об ошибках
   - Логи
