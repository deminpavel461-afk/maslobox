# MasloBox API

Backend для приёма заявок с лендинга и передачи их администраторам точек.

## Стек

- FastAPI + Pydantic
- SQLAlchemy 2 + SQLite (по умолчанию)
- Уведомления: console / email-stub / telegram-mock (без внешних API)

## Запуск

```bash
cd backend
# PATH к uv, если ещё не добавлен:
# $env:Path = "C:\Users\паша\.local\bin;$env:Path"

uv sync
uv run uvicorn backend.main:app --reload --port 8000
```

Документация: http://127.0.0.1:8000/docs

Прод на Timeweb Cloud: см. [`../DEPLOY-TIMEWEB.md`](../DEPLOY-TIMEWEB.md).

## Публичное API

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/api/v1/points` | Активные точки |
| GET | `/api/v1/services` | Услуги и цены |
| POST | `/api/v1/bookings` | Создание заявки |
| GET | `/api/v1/reviews` | Опубликованные отзывы |

### Валидация заявки

- имя 2–50 символов
- телефон нормализуется к `+7XXXXXXXXXX`
- марка/модель обязательна
- `consent: true` обязателен
- желаемое время: если распарсилось — проверка режима работы точки
- rate limit: 3 заявки / телефон / 10 мин, 5 / IP / 10 мин
- honeypot-поле `website` (заполненное → заявка не сохраняется)

Ошибки `422`:

```json
{
  "detail": [
    {"field": "phone", "message": "Укажите корректный российский телефон..."}
  ]
}
```

## Админка

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/api/v1/admin/bookings` | Список с фильтрами и пагинацией |
| PATCH | `/api/v1/admin/bookings/{id}` | Статус / комментарий админа |

Авторизация:

- супер-админ: `Authorization: Bearer change-me-admin-token`
- админ точки: `X-Admin-Token: north-token` (или `center-token`, `south-token`)

Статусы: `new → confirmed → done | canceled`.

## Уведомления

Интерфейс `Notifier.notify_new_booking(...)`.

Реализации (включаются через `NOTIFICATION_CHANNELS`):

- `console` — print/лог
- `email` — заглушка outbox в памяти
- `telegram` — мок сообщений бота

## Тесты

```bash
uv sync --group dev
uv run pytest -q
```
