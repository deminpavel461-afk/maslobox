# Деплой МаслоБокс на Timeweb Cloud (App Platform)

Timeweb App Platform **не поддерживает docker-compose**. Нужен один `Dockerfile` в корне репозитория (уже есть) и GitHub / GitLab / Bitbucket.

## Что уйдёт в прод

- лендинг (`/`)
- API (`/api/v1/...`, docs: `/docs`)
- SQLite по умолчанию в `/data/maslobox.db` (диск контейнера; для продакшена лучше позже подключить managed DB)

## 1. Репозиторий

1. Создайте пустой репозиторий на GitHub (например `maslobox`).
2. Залейте проект:

```bash
cd Documents/maslobox
git init -b main
git add .
git commit -m "MasloBox landing + API ready for Timeweb"
git remote add origin https://github.com/<USER>/maslobox.git
git push -u origin main
```

## 2. Панель Timeweb Cloud

1. Откройте [Timeweb Cloud → App Platform](https://timeweb.cloud/my/apps) → **Создать**.
2. Подключите GitHub/GitLab/Bitbucket и выберите репозиторий `maslobox`, ветка `main`.
3. Фреймворк: **Dockerfile**.
4. Путь до проекта: корень (пусто / `.`).
5. Регион и тариф — на ваш выбор (для старта хватит минимального backend-пресета).
6. Переменные окружения (обязательно смените токен):

| Ключ | Значение |
|------|----------|
| `ADMIN_TOKEN` | длинный секрет |
| `NOTIFICATION_CHANNELS` | `console,email,telegram` |
| `CORS_ORIGINS` | `["*"]` или ваш домен |
| `DATABASE_URL` | `sqlite:////data/maslobox.db` |
| `PORT` | `8080` (обычно не нужно, Dockerfile сам слушает 8080) |

7. Запустите деплой. Дождитесь статуса **started**.
8. Откройте выданный `*.timeweb.cloud` / технический домен по HTTPS.

Проверки после деплоя:

- `GET /health` → `{"status":"ok"}`
- `GET /api/v1/points` → 3 точки
- форма «Записаться» на главной создаёт заявку
- веб-админка: `https://<домен>/admin/` — вход по `ADMIN_TOKEN`
- API админки: `Authorization: Bearer <ADMIN_TOKEN>` на `GET /api/v1/admin/bookings`

## 3. Через CLI (опционально)

```bash
pip install twc
twc config set --api-token <TIMEWEB_API_TOKEN>
twc apps get-vcs-providers
twc apps get-repositories "<provider_id>"
twc apps list-presets backend
# заполните deploy/timeweb-app.example.yml → timeweb-app.yml
twc apps create deploy/timeweb-app.yml
```

Токен API: панель Timeweb Cloud → профиль → API.

## 4. Домен

В App Platform можно привязать свой домен и SSL. После привязки форма уже ходит на относительный `/api/v1` — менять URL в фронте не нужно.

## 5. Важно про данные

SQLite внутри контейнера может обнулиться при пересоздании приложения. Для боевого трафика:

- подключите Timeweb Managed PostgreSQL и задайте `DATABASE_URL=postgresql+psycopg://...`, или
- сделайте регулярный бэкап файла БД / выгрузку заявок через админ API.
