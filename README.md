# CineBot — Корпоративный Telegram-бот для кинокомпании

Telegram-бот для управления событиями (премьеры, встречи, дни рождения) и поиска файлов на Яндекс.Диске.

## Возможности

- ✅ Добавление событий через пошаговый диалог (FSM)
- ✅ Просмотр ближайших событий
- ✅ Удаление событий
- ✅ Автоматические напоминания за N дней до события
- ✅ Поиск файлов на Яндекс.Диске
- ✅ Кэширование файлов для быстрого поиска
- ✅ **LLM-агент для общения на естественном языке** (OpenRouter API)

## Стек технологий

- Python 3.12
- aiogram 3.x — Telegram Bot API
- PostgreSQL 16 — база данных
- SQLAlchemy 2.x + asyncpg — ORM
- Alembic — миграции БД
- APScheduler — планировщик задач
- yadisk — интеграция с Яндекс.Диском
- LangChain + OpenRouter — LLM-агент для естественного языка
- Docker Compose — оркестрация

## Быстрый старт

### 1. Клонирование и настройка

```bash
git clone <repository-url>
cd cine-bot
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните реальными значениями:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
# Telegram
BOT_TOKEN=your_real_bot_token_from_@BotFather
GROUP_CHAT_ID=-1001234567890  # ID вашей группы

# PostgreSQL (можно оставить как есть)
POSTGRES_USER=cinebot
POSTGRES_PASSWORD=secretpassword
POSTGRES_DB=cinebot_db
DATABASE_URL=postgresql+asyncpg://cinebot:secretpassword@db:5432/cinebot_db

# Яндекс.Диск
YANDEX_DISK_TOKEN=your_yandex_disk_oauth_token

# LLM (OpenRouter) - опционально
OPENROUTER_API_KEY=your_openrouter_api_key
LLM_MODEL=openrouter/hunter-alpha
LLM_BASE_URL=https://openrouter.ai/api/v1
```

### 3. Получение токенов

#### Telegram Bot Token
1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Создайте нового бота командой `/newbot`
3. Скопируйте полученный токен в `BOT_TOKEN`

#### Group Chat ID
1. Добавьте бота в вашу группу
2. Напишите что-нибудь в группе
3. Откройте `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Найдите `"chat":{"id":-1001234567890}` и скопируйте ID

#### Yandex.Disk Token
1. Перейдите на [OAuth Яндекса](https://oauth.yandex.ru/)
2. Зарегистрируйте приложение
3. Получите токен с правами на чтение Диска

#### OpenRouter API Key (опционально, для LLM-агента)
1. Зарегистрируйтесь на [OpenRouter](https://openrouter.ai/)
2. Получите API ключ
3. Добавьте в `.env` как `OPENROUTER_API_KEY`

**Примечание:** LLM-агент опционален. Без него бот работает через команды.

### 4. Запуск через Docker

```bash
# Запуск всех сервисов
docker compose up -d

# Просмотр логов
docker compose logs -f bot

# Остановка
docker compose down
```

### 5. Применение миграций

Миграции применяются автоматически при запуске бота. Если нужно применить вручную:

```bash
docker compose exec bot alembic upgrade head
```

## Команды бота

- `/start` — Запустить бота
- `/help` — Справка по командам
- `/addevent` — Добавить событие (пошаговый диалог)
- `/events` — Показать ближайшие события
- `/delevent` — Удалить событие
- `/find <запрос>` — Найти файл на Яндекс.Диске
- `/cancel` — Отменить текущее действие

**Новое:** Можно общаться с ботом на естественном языке без команд!
Примеры: "Добавь премьеру фильма Горизонт 20 апреля в 19:00", "Покажи ближайшие события", "Найди сценарий"
См. [LLM_EXAMPLES.md](LLM_EXAMPLES.md) для подробностей.

## Примеры использования

### Добавление события

```
Вы: /addevent
Бот: 📝 Введите название события:
Вы: Премьера фильма «Горизонт»
Бот: 📅 Введите дату: ДД.ММ.ГГГГ ЧЧ:ММ
Вы: 20.04.2026 19:00
Бот: [показывает кнопки с типами событий]
Вы: 🎬 Премьера
Бот: ⏰ За сколько дней напомнить?
Вы: 2
Бот: ✅ Событие добавлено!
```

### Поиск файла

```
Вы: /find сценарий Горизонт
Бот: 📁 Найдено: Горизонт_Сценарий_финал.pdf
     🔗 [ссылка на файл]
```

## Разработка

### Локальный запуск без Docker

```bash
# Создание виртуального окружения
python3.12 -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Запуск PostgreSQL отдельно
docker compose up -d db

# Применение миграций
alembic upgrade head

# Запуск бота
python -m app.main
```

### Структура проекта

```
cine-bot/
├── app/
│   ├── main.py              # Точка входа
│   ├── config.py            # Настройки
│   ├── scheduler.py         # Планировщик задач
│   ├── db/
│   │   ├── base.py          # База данных
│   │   └── models.py        # Модели SQLAlchemy
│   ├── states/
│   │   └── event_states.py  # FSM состояния
│   ├── services/
│   │   ├── event_service.py     # Работа с событиями
│   │   ├── reminder_service.py  # Напоминания
│   │   └── yadisk_service.py    # Яндекс.Диск
│   └── handlers/
│       ├── common.py        # Общие команды
│       ├── events.py        # Управление событиями
│       └── files.py         # Поиск файлов
├── alembic/                 # Миграции БД
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env
```

## Планировщик задач

Бот автоматически выполняет следующие задачи:

- **09:00 ежедневно** — Проверка событий и отправка напоминаний
- **03:00 ежедневно** — Синхронизация кэша файлов с Яндекс.Диска

## Troubleshooting

### Бот не отвечает
- Проверьте, что бот запущен: `docker compose ps`
- Проверьте логи: `docker compose logs bot`
- Убедитесь, что токен бота правильный

### Ошибка подключения к БД
- Проверьте, что PostgreSQL запущен: `docker compose ps db`
- Проверьте `DATABASE_URL` в `.env`

### Не работает поиск файлов
- Проверьте токен Яндекс.Диска
- Запустите синхронизацию вручную (будет добавлено в следующей версии)

## Roadmap

- [x] ~~Этап 7: LLM-агент для парсинга команд на естественном языке~~ ✅ Реализовано!
- [ ] Команда для ручной синхронизации Яндекс.Диска
- [ ] Права доступа (только админы могут добавлять события)
- [ ] Экспорт событий в календарь
- [ ] Уведомления в несколько этапов (за 7, 3, 1 день)

## Лицензия

MIT
