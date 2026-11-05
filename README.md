# jobtracker-api

REST API для учёта вакансий и откликов: добавляешь вакансию, отмечаешь отклик,
видишь сводку по статусам. Сделан как учебный backend-проект на стеке
Python / FastAPI / SQLAlchemy 2.0 / PostgreSQL.

## Стек

| Слой | Технология |
|---|---|
| HTTP | FastAPI, Pydantic v2 |
| БД | PostgreSQL 16, SQLAlchemy 2.0 (typed ORM), psycopg 3 |
| Миграции | Alembic |
| Тесты | pytest, FastAPI TestClient, SQLite в памяти |
| Инфраструктура | Docker, docker-compose, uv |

## Структура

```
app/
  main.py        сборка приложения, /health
  config.py      настройки из env (pydantic-settings, префикс JT_)
  db.py          engine, sessionmaker, Base, зависимость get_db
  models.py      ORM: Vacancy, Application, VacancyStatus
  schemas.py     схемы запросов/ответов и валидация
  crud.py        вся логика работы с БД (без HTTP)
  api/
    vacancies.py роутер /vacancies и /vacancies/{id}/applications
    stats.py     роутер /stats
alembic/         миграции
tests/           тесты API на SQLite в памяти
```

Логика отделена от HTTP: `crud.py` не знает про `HTTPException`, роутеры только
переводят доменные ошибки (`DuplicateUrl`, `AlreadyApplied`) в коды 409.

## Запуск

### Вариант 1: docker-compose (нужен запущенный Docker)

```bash
docker compose up --build
```

Поднимается PostgreSQL и API; миграции применяются на старте.
Документация Swagger: http://localhost:8000/docs

### Вариант 2: локально

```bash
uv sync
cp .env.example .env          # или export JT_DATABASE_URL=...
uv run alembic upgrade head   # создать таблицы
uv run uvicorn app.main:app --reload
```

### Вариант 3: PostgreSQL без root (rootless)

Если ставить пакет в систему нельзя, бинарники PostgreSQL 18.6 лежат в
`~/.local/share/pgrootless` и запускаются от пользователя:

```bash
scripts/pg.sh start     # 127.0.0.1:55432
scripts/pg.sh status
scripts/pg.sh stop

export JT_DATABASE_URL=postgresql+psycopg://jobtracker@127.0.0.1:55432/jobtracker
uv run alembic upgrade head
```

Системная установка (если sudo доступен) — `sudo bash scripts/setup-postgres.sh`:
пакет, `initdb`, служба, роль и база создаются идемпотентно.

## Эндпоинты

| Метод | Путь | Что делает |
|---|---|---|
| GET | `/health` | проверка живости |
| POST | `/vacancies` | добавить вакансию (201, 409 если URL уже есть) |
| GET | `/vacancies` | список: `status`, `remote`, `q`, `limit`, `offset` |
| GET | `/vacancies/{id}` | одна вакансия (404 если нет) |
| PATCH | `/vacancies/{id}` | частичное обновление |
| DELETE | `/vacancies/{id}` | удалить вместе с откликами (204) |
| POST | `/vacancies/{id}/applications` | отправить отклик (409 на повтор) |
| GET | `/vacancies/{id}/applications` | отклики по вакансии |
| GET | `/stats` | всего вакансий, счётчики по статусам, число откликов |

### Пример

```bash
curl -X POST localhost:8000/vacancies \
  -H 'Content-Type: application/json' \
  -d '{"title":"Backend-разработчик (Python)","company":"Ромашка",
       "url":"https://hh.ru/vacancy/777","salary_from":60000,
       "salary_to":90000,"remote":true}'

curl -X POST localhost:8000/vacancies/1/applications \
  -H 'Content-Type: application/json' \
  -d '{"cover_letter":"Здравствуйте! Готов работать по ГПХ."}'

curl 'localhost:8000/vacancies?status=applied&remote=true'
curl localhost:8000/stats
```

## Тесты

```bash
uv run pytest
```

12 тестов: CRUD, фильтры и пагинация, валидация диапазона зарплат (в том числе
при частичном PATCH), конфликт по уникальному URL, однократность отклика
и смена статуса, счётчики статистики. Тесты идут на SQLite в памяти через
`dependency_overrides` — Postgres для прогона не нужен.

## Решения, которые стоит объяснить на собеседовании

- **Уникальный URL вакансии** не даёт добавить один и тот же пост дважды;
  нарушение ловится на уровне БД (`IntegrityError` → 409), а не проверкой
  «прочитать и сравнить», поэтому гонка двух запросов не проходит.
- **Отклик меняет статус вакансии** на `applied` в одной транзакции с
  созданием записи: не бывает «отклик есть, а статус старый».
- **Частичный PATCH проверяет диапазон зарплат на итоговых значениях**, иначе
  `{"salary_from": 200000}` при `salary_to: 120000` дал бы битые данные.
- **`pool_pre_ping=True`**: Postgres рвёт простаивающие соединения, без проверки
  первый запрос после паузы падает.
- **Статусы без записей отдаются нулями** в `/stats` — фронту не нужно
  подставлять отсутствующие ключи.

## Что дальше

- Аутентификация (JWT) и привязка вакансий к пользователю
- Курсорная пагинация вместо offset на больших объёмах
- CI (GitHub Actions): lint + pytest на каждый пуш
