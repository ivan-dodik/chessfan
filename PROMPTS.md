# Prompts history

## Initial DB plan generation

Prompt to agent in plan mode:

```text
Ты — ИТ-архитектор и разработчик баз данных. Твоя задача — спланировать создание базы данных для MVP сервиса мониторинга офлайн-шахматных турниров.

Целевая аудитория финального решения: начинающий разработчик БД, который будет разворачивать и использовать эту БД.

Ключевые требования к БД:
- Только необходимый минимум для работающего MVP.
- Без избыточной сложности (никаких партиционирований, GIN-индексов, материализованных представлений, soft delete, отдельный справочников федераций/титулов).
- Поддержка истории рейтингов (с возможностью узнать рейтинг игрока на любую дату).
- Поддержка истории турнирных положений (snapshot после каждого тура).
- Учёт ситуации "bye" — игрок получает очко без партии.
- Live-уведомления через pg_notify при изменении результата партии.

Ограничения со стороны заказчика:
- Нет точного времени начала/окончания партий и туров (только даты турниров).
- Нет PGN-нотаций в MVP.
- Нет what-if прогнозов.
- Нет created_at/updated_at в большинстве таблиц (кроме критических для отладки).
- Нет полей played_at, started_at, finished_at.

Требования к результату планирования:

1. Перечисли все необходимые таблицы с обоснованием, зачем каждая нужна в MVP.

2. Для каждой таблицы опиши:
   - Назначение (1-2 предложения).
   - Список полей с типами данных и кратким комментарием.
   - Первичные и внешние ключи.
   - Почему выбраны именно такие поля (почему чего-то нет).

3. Опиши необходимые индексы (только самые нужные: по FK, для поиска активного турнира, для текущего рейтинга).

4. Опиши представления (views), которые нужны для UI: активная турнирная таблица, карточка игрока.

5. Опиши триггер и функцию для pg_notify при изменении результата партии.

6. Опиши, кто и как должен обновлять таблицу tournament_standings (скрипт, не БД).

7. Приведи полный SQL-скрипт для создания всех объектов БД в правильном порядке (с учётом зависимостей по внешним ключам).

8. Добавь краткую инструкцию для начинающего разработчика:
   - Как выполнить скрипт.
   - Какие данные и в каком порядке нужно загружать.
   - Как учесть bye при загрузке партий.
   - Как проверить, что уведомления работают.

Формат ответа:
- Чёткие разделы с заголовками.
- SQL-код в отдельных блоках с синтаксисом PostgreSQL.
- Таблицы и поля — в текстовых таблицах или списках (удобно для чтения).
- Диаграмма Mermaid по желанию, но не обязательна.

Дополнительные условия:
- Использовать синтаксис PostgreSQL 13+.
- Все идентификаторы — snake_case.
- Ограничения (CHECK, NOT NULL, UNIQUE) указывать явно.
- Комментарии к полям таблиц — на русском или английском (на твой выбор), но понятно.

Важно: не добавляй ничего, что не входит в MVP. Если сомневаешься — не добавляй.

Требования

* cохраняй историю промптов в файле PROMTS.md
* веди журнал изменений в файле CHANGES.md
```

### Update 1: Schema modifications

Prompt to agent in plan mode:

```text
Удали федерацию и доп. коэффициенты (tiebreaks). Добавь в план генерацию и описания БД в каталоге docs/db
Вместо fide_id сделай rus_id. Добавь город игрока. В таблице партии поля white_score и black_score избыточны, замени одним, т.к. 1 у белых - это ноль у чёрных и наоборот. Ничья - пополам.
```

Changes made:
- Removed `federation` column from `tournament_players` table
- Removed `tiebreak1`, `tiebreak2` columns from `tournament_standings` table
- Changed `fide_id` to `rus_id` in `players` table
- Added `city` column to `players` table
- Replaced `white_score` and `black_score` with single `score` column in `games` table
- Created documentation structure in `docs/db/` directory
- Created SQL script at `docs/db/sql/create.sql`
- Created documentation files: README.md, schema.md, views.md, triggers.md
```

## DB implementation

Prompt to agent in act mode:

```text
Реализуй создание базы данных Chessfan MVP согласно спланированной схеме.

Требования:
1. Создать каталог docs/db с подкаталогами
2. Создать файл docs/db/README.md с инструкциями по установке
3. Создать файл docs/db/schema.md с описанием схемы БД
4. Создать файл docs/db/sql/create.sql с полным SQL-скриптом
5. Создать файл docs/db/views.md с описанием представлений
6. Создать файл docs/db/triggers.md с описанием триггеров и уведомлений
7. Обновить файл PROMPTS.md с историей промптов
8. Создать файл CHANGES.md с журналом изменений

SQL-скрипт должен создавать:
- 6 таблиц: players, tournaments, tournament_players, games, player_ratings, tournament_standings
- 11 индексов для оптимизации запросов
- 3 представления: v_active_tournament_table, v_player_profile, v_player_rating_history
- 1 функцию и триггер для pg_notify при изменении результатов партий

Все идентификаторы в snake_case. PostgreSQL 13+.
```

Changes made:
- Created docs/db/ directory structure
- Created docs/db/README.md with installation instructions
- Created docs/db/schema.md with database schema description
- Created docs/db/sql/create.sql with complete SQL script
- Created docs/db/views.md with views documentation
- Created docs/db/triggers.md with triggers and notifications documentation
- Updated PROMPTS.md with history
- Created CHANGES.md with changelog
```

## Docker Compose for PostgreSQL

Prompt to agent in plan mode:

```text
Подготовь файл Docker Compose для подъёма сервера PostgreSQL на котором будет работать база данных проекта.

Следуй свои указаниям по об更新лению файлов с промптами и изменениями. Документацию создай в docs/deployment
```

Prompt to agent in act mode:

```text
Создай Docker Compose конфигурацию для PostgreSQL и обнови документацию.

Требования:
1. Создать docker-compose.yml для PostgreSQL 15
2. Создать .env.example с примерами переменных
3. Создать docs/deployment/docker.md с инструкциями по развертыванию
4. Обновить docs/db/README.md для упоминания Docker-подхода
5. Обновить CHANGES.md с записью о Docker Compose
6. Обновить PROMPTS.md с историей промптов

Конфигурация должна включать:
- PostgreSQL 15
- База данных: chessfan
- Пользователь: chessfan
- Автоматическая инициализация через docs/db/sql/create.sql
- Постоянное хранилище данных
```

Changes made:
- Created docker-compose.yml with PostgreSQL 15 configuration
- Created .env.example with environment variables
- Created docs/deployment/docker.md with comprehensive Docker deployment guide
- Updated docs/db/README.md to include Docker quick start option
- Updated CHANGES.md with Docker Compose entry
- Updated PROMPTS.md with this history
```
