# CineBot — Корпоративный Telegram-бот для кинокомпании

## Стек технологий

- **Python 3.12** — основной язык
- **aiogram 3.x** — Telegram Bot API framework
- **PostgreSQL 16** — хранение данных
- **SQLAlchemy 2.x + asyncpg** — ORM и async-драйвер
- **Alembic** — миграции БД
- **APScheduler** — планировщик задач (напоминания)
- **yadisk** — Python SDK для Яндекс.Диска
- **LangChain / OpenAI API** — LLM для парсинга (добавляется позже)
- **Docker Compose** — оркестрация сервисов

---

## Архитектура системы

```
Telegram Chat
     │
     ▼
aiogram (bot service)
     │
     ├── FSM Handlers (команды /addevent, /events и т.д.)
     │        └── пошаговый диалог через состояния
     │
     ├── [Этап 6] LLM Agent (OpenAI / local LLM)
     │        └── парсинг команд из естественного языка
     │        └── вызывает те же event_service функции
     │
     ├── Event Service
     │        └── CRUD событий, дней рождений, встреч
     │
     ├── Reminder Service
     │        └── APScheduler → отправка уведомлений
     │
     └── Yandex.Disk Service
              └── поиск файлов → возврат ссылок
```

---

## Структура проекта

```
cinebot/
├── docker-compose.yml
├── .env
├── alembic/
│   ├── env.py
│   └── versions/
├── app/
│   ├── main.py                   # точка входа, регистрация роутеров
│   ├── config.py                 # настройки через pydantic-settings
│   ├── db/
│   │   ├── base.py               # Base, engine, session
│   │   └── models.py             # модели БД
│   ├── states/
│   │   └── event_states.py       # FSM-состояния
│   ├── services/
│   │   ├── event_service.py      # CRUD событий
│   │   ├── reminder_service.py   # планировщик напоминаний
│   │   └── yadisk_service.py     # интеграция с Яндекс.Диском
│   ├── agent/                    # [Этап 6] LLM-агент
│   │   ├── llm_agent.py
│   │   └── tools.py
│   ├── handlers/
│   │   ├── common.py             # /start, /help, /cancel
│   │   ├── events.py             # /addevent, /events, /delevent
│   │   └── files.py              # /find — поиск файлов на Диске
│   └── scheduler.py              # инициализация APScheduler
├── requirements.txt
└── Dockerfile
```

---

## База данных

### Таблица `events`

| Поле        | Тип          | Описание                                   |
|-------------|--------------|--------------------------------------------|
| id          | SERIAL PK    | Первичный ключ                             |
| title       | VARCHAR(255) | Название события                           |
| event_type  | VARCHAR(50)  | `meeting`, `birthday`, `premiere`, `other` |
| event_date  | TIMESTAMP    | Дата и время события                       |
| description | TEXT         | Описание (опционально)                     |
| chat_id     | BIGINT       | Telegram chat_id для напоминания           |
| remind_days | INTEGER      | За сколько дней напоминать (дефолт: 2)     |
| is_notified | BOOLEAN      | Флаг отправки напоминания                  |
| created_at  | TIMESTAMP    | Время создания записи                      |

### Таблица `yandex_files_cache`

| Поле       | Тип          | Описание                                 |
|------------|--------------|------------------------------------------|
| id         | SERIAL PK    | Первичный ключ                           |
| file_name  | VARCHAR(500) | Имя файла на Диске                       |
| file_path  | TEXT         | Полный путь на Яндекс.Диске              |
| public_url | TEXT         | Публичная ссылка                         |
| file_type  | VARCHAR(50)  | `video`, `photo`, `document`, `scenario` |
| updated_at | TIMESTAMP    | Время последней синхронизации            |

---

## Docker Compose

```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U ${POSTGRES_USER}" ]
      interval: 5s
      retries: 5

  bot:
    build: .
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    command: python -m app.main

volumes:
  postgres_data:
```

---

## .env (шаблон)

```env
# Telegram
BOT_TOKEN=your_telegram_bot_token
GROUP_CHAT_ID=-100xxxxxxxxxx

# PostgreSQL
POSTGRES_USER=cinebot
POSTGRES_PASSWORD=secretpassword
POSTGRES_DB=cinebot_db
DATABASE_URL=postgresql+asyncpg://cinebot:secretpassword@db:5432/cinebot_db

# Яндекс.Диск
YANDEX_DISK_TOKEN=your_yandex_disk_oauth_token

# LLM (добавить на Этапе 6)
OPENAI_API_KEY=your_openai_key
LLM_MODEL=gpt-4o-mini
```

---

## Этапы разработки

### Этап 1 — Инфраструктура (2–3 дня)

- [ ] Создать репозиторий, настроить `.gitignore`
- [ ] Написать `docker-compose.yml` и `Dockerfile`
- [ ] Настроить `config.py` через `pydantic-settings`
- [ ] Подключить SQLAlchemy + asyncpg
- [ ] Создать модели БД (`events`, `yandex_files_cache`)
- [ ] Первая миграция через Alembic
- [ ] Запустить `docker compose up`, проверить соединение с БД

### Этап 2 — Базовый бот (1–2 дня)

- [ ] Инициализация aiogram, polling в `main.py`
- [ ] Регистрация команд через `set_my_commands`:
    - `/addevent` — добавить событие
    - `/events` — ближайшие события
    - `/delevent` — удалить событие
    - `/find` — найти файл на Яндекс.Диске
    - `/cancel` — отменить текущее действие
    - `/help` — справка
- [ ] Хэндлер `/start` и `/help`
- [ ] Хэндлер `/cancel` — сброс любого FSM-состояния

### Этап 3 — Добавление событий через FSM (2–3 дня)

- [ ] Создать `app/states/event_states.py`:
  ```python
  class AddEventFSM(StatesGroup):
      waiting_for_title       = State()
      waiting_for_date        = State()
      waiting_for_type        = State()
      waiting_for_remind_days = State()
  ```
- [ ] Хэндлер `/addevent` — запуск FSM, проверка роли (только админы группы)
- [ ] Шаг 1: запросить название → сохранить в `state.update_data`
- [ ] Шаг 2: запросить дату в формате `ДД.ММ.ГГГГ ЧЧ:ММ` → валидация через `strptime`, повтор при ошибке
- [ ] Шаг 3: выбор типа события через `ReplyKeyboardMarkup`:
    - `🎬 Премьера` / `📅 Встреча` / `🎂 День рождения` / `📌 Другое`
- [ ] Шаг 4: за сколько дней напомнить (число или `0`) → сохранить событие в БД
- [ ] Подтверждение: вывести итоговую карточку события
- [ ] Реализовать `event_service.create_event()` и `event_service.get_upcoming_events()`

### Этап 4 — Просмотр и удаление событий (1–2 дня)

- [ ] `/events` — вывод ближайших N событий из БД, сгруппированных по типу
- [ ] `/delevent` — список событий с нумерацией, ввод номера для удаления
- [ ] Формат карточки события:
  ```
  🎬 Премьера «Горизонт»
  📅 20.04.2026 в 19:00
  ⏰ Напоминание за 2 дня
  ```

### Этап 5 — Напоминания (2 дня)

- [ ] Настроить `APScheduler` с `AsyncIOScheduler` в `scheduler.py`
- [ ] Job: каждый день в 09:00 — проверить события, отправить напоминание за N дней
- [ ] Формат уведомления:
  ```
  🔔 Напоминание!
  Через 2 дня: Премьера «Горизонт»
  📅 20 апреля 2026 в 19:00
  ```
- [ ] После отправки проставлять `is_notified = true`
- [ ] Обработать повторный запуск: не слать уже отправленные напоминания

### Этап 6 — Интеграция с Яндекс.Диском (3–4 дня)

- [ ] Получить OAuth-токен Яндекс.Диска, подключить `yadisk`
- [ ] Рекурсивный обход папок → кэшировать файлы в `yandex_files_cache`
- [ ] Job: раз в сутки обновлять кэш
- [ ] Хэндлер `/find <запрос>` — fuzzy-поиск по `file_name` в кэше
- [ ] Возврат публичной ссылки в чат:
  ```
  📁 Найдено: Горизонт_Сценарий_v3.pdf
  🔗 https://disk.yandex.ru/d/xxxx
  ```
- [ ] Обработка случая "файл не найден"

### Этап 7 — LLM-агент (3–4 дня, опционально)

> Добавляется поверх готовой базы. Все существующие хэндлеры и сервисы остаются без изменений.

- [ ] Подключить LangChain + OpenAI API
- [ ] Написать системный промпт для русскоязычного парсинга
- [ ] Создать инструменты агента (`tools.py`), которые вызывают уже готовые сервисы:
    - `add_event(title, date, type, remind_days)` → `event_service.create_event()`
    - `search_file(query)` → `yadisk_service.search()`
    - `list_events(period)` → `event_service.get_upcoming_events()`
- [ ] Хэндлер обычных сообщений в группе → передавать в LLM-агент
- [ ] Тест: `"Добавь премьеру фильма Горизонт 20 апреля в 19:00"` → агент вызывает `add_event`
- [ ] Fallback: если агент не распознал команду → вернуть `/help`

### Этап 8 — Тестирование и деплой (1–2 дня)

- [ ] End-to-end тесты всех сценариев в тестовой группе
- [ ] Настроить логирование через `loguru`
- [ ] Обработка всех ошибок, fallback-ответы
- [ ] Деплой на VPS: `docker compose up -d`
- [ ] Проверить автоперезапуск при сбое

---

## Ключевые сценарии использования

### Сценарий 1: Добавление события через команду (FSM)

```
Пользователь: /addevent
Бот: 📝 Введите название события:
Пользователь: Премьера фильма «Горизонт»
Бот: 📅 Введите дату: ДД.ММ.ГГГГ ЧЧ:ММ
Пользователь: 20.04.2026 19:00
Бот: [кнопки типа события]
Пользователь: 🎬 Премьера
Бот: ⏰ За сколько дней напомнить?
Пользователь: 2
Бот: ✅ Событие добавлено! Премьера «Горизонт» — 20.04.2026 в 19:00
```

### Сценарий 2: Добавление события через LLM (Этап 7)

```
Пользователь: Добавь премьеру фильма Горизонт 20 апреля в 19:00
Бот: ✅ Событие добавлено! Премьера «Горизонт» — 20.04.2026 в 19:00
```

### Сценарий 3: Поиск файла

```
Пользователь: /find сценарий Горизонт
Бот: 📁 Найдено: Горизонт_Сценарий_финал.pdf
     🔗 https://disk.yandex.ru/d/...
```

### Сценарий 4: Автоматическое напоминание

```
Бот (09:00): 🔔 Напоминание!
             Через 2 дня: Премьера «Горизонт»
             📅 20 апреля 2026 в 19:00
```

---
