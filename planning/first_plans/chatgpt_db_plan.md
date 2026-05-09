Ниже — проект БД под задачу мониторинга офлайн-шахматных турниров с акцентом на:

* историчность рейтингов;
* потоковое обновление активных турниров;
* расчёт прогнозов внешними сервисами;
* удобные выборки для UI и аналитики;
* возможность хранить «живую» информацию от болельщиков/наблюдателей.

---

# Архитектурный подход

## Основные принципы

### 1. PostgreSQL как OLTP + лёгкая аналитика

База хранит:

* нормализованные сущности;
* историю изменений;
* результаты туров;
* агрегаты/витрины.

Сложные расчёты:

* прогноз мест;
* модели «что если»;
* Elo/FIDE performance;
* вероятности исходов

выполняются внешними сервисами.

---

### 2. Разделение:

## «Справочник» vs «События»

### Справочники

Редко меняются:

* шахматисты;
* федерации;
* турниры;
* контроль времени;
* города.

### События

Постоянно обновляются:

* туры;
* партии;
* промежуточные таблицы;
* рейтинги;
* прогнозы.

---

### 3. Историчность обязательна

Нельзя хранить только текущее состояние.

Например:

* рейтинг сегодня ≠ рейтинг месяц назад;
* место после 3 тура ≠ итоговое место.

Поэтому:

* отдельные таблицы истории;
* snapshot-подход для турнирных standings.

---

# Общая схема сущностей

```text
players
  └── player_ratings
  └── tournament_players
          └── tournament_standings
          └── games

tournaments
  └── tournament_rounds
  └── tournament_players
  └── games

games
  └── game_moves (опционально)
  └── game_events

external_sources
ingestion_logs
```

---

# Ключевые таблицы

---

# 1. players — шахматисты

Главная сущность.

```sql
CREATE TABLE players (
    id BIGSERIAL PRIMARY KEY,

    external_ru_id BIGINT,          -- id на сайте ФШР
    fide_id BIGINT,

    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,

    full_name TEXT GENERATED ALWAYS AS (
        trim(last_name || ' ' || first_name || ' ' || coalesce(middle_name, ''))
    ) STORED,

    sex CHAR(1),                    -- M/F
    birth_date DATE,

    federation_code VARCHAR(3),     -- RUS, KAZ ...

    city TEXT,
    region TEXT,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
```

## Индексы

```sql
CREATE INDEX idx_players_fide_id
    ON players(fide_id);

CREATE INDEX idx_players_external_ru_id
    ON players(external_ru_id);

CREATE INDEX idx_players_full_name
    ON players(full_name);
```

---

# 2. player_ratings — история рейтингов

Рейтинг меняется после турнира → нужна история.

```sql
CREATE TABLE player_ratings (
    id BIGSERIAL PRIMARY KEY,

    player_id BIGINT NOT NULL REFERENCES players(id),

    rating_type VARCHAR(20) NOT NULL,
    -- standard / rapid / blitz

    rating_value INTEGER NOT NULL,

    valid_from DATE NOT NULL,
    valid_to DATE,

    source VARCHAR(50), -- FSHR / FIDE

    created_at TIMESTAMP DEFAULT now()
);
```

## Почему interval validity

Это позволяет:

* получить рейтинг на дату турнира;
* строить график изменений;
* анализировать прогресс.

---

# 3. tournaments — турниры

```sql
CREATE TABLE tournaments (
    id BIGSERIAL PRIMARY KEY,

    external_chess_results_id BIGINT,

    name TEXT NOT NULL,

    city TEXT,
    region TEXT,
    country_code VARCHAR(3),

    start_date DATE,
    end_date DATE,

    time_control_type VARCHAR(20),
    -- classical / rapid / blitz

    rounds_count INTEGER,

    chief_judge TEXT,

    source_url TEXT,

    is_active BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

---

# 4. tournament_rounds — туры

```sql
CREATE TABLE tournament_rounds (
    id BIGSERIAL PRIMARY KEY,

    tournament_id BIGINT NOT NULL
        REFERENCES tournaments(id),

    round_number INTEGER NOT NULL,

    started_at TIMESTAMP,
    finished_at TIMESTAMP,

    status VARCHAR(20),
    -- planned / active / finished

    UNIQUE(tournament_id, round_number)
);
```

---

# 5. tournament_players — участие игрока в турнире

Очень важная таблица.

```sql
CREATE TABLE tournament_players (
    id BIGSERIAL PRIMARY KEY,

    tournament_id BIGINT NOT NULL
        REFERENCES tournaments(id),

    player_id BIGINT NOT NULL
        REFERENCES players(id),

    seed_number INTEGER,
    start_rank INTEGER,

    initial_rating INTEGER,

    title VARCHAR(10),
    -- GM / IM / FM ...

    federation_code VARCHAR(3),

    created_at TIMESTAMP DEFAULT now(),

    UNIQUE(tournament_id, player_id)
);
```

---

# 6. games — партии

Центральная таблица.

```sql
CREATE TABLE games (
    id BIGSERIAL PRIMARY KEY,

    tournament_id BIGINT NOT NULL
        REFERENCES tournaments(id),

    round_id BIGINT NOT NULL
        REFERENCES tournament_rounds(id),

    board_number INTEGER,

    white_player_id BIGINT NOT NULL
        REFERENCES players(id),

    black_player_id BIGINT NOT NULL
        REFERENCES players(id),

    result VARCHAR(10),
    -- 1-0 / 0-1 / 1/2-1/2 / forfeit

    result_status VARCHAR(20),
    -- scheduled / active / finished

    moves_pgn TEXT,

    white_rating INTEGER,
    black_rating INTEGER,

    played_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);
```

---

# 7. game_events — события партии

Для live-режима.

```sql
CREATE TABLE game_events (
    id BIGSERIAL PRIMARY KEY,

    game_id BIGINT NOT NULL
        REFERENCES games(id),

    event_type VARCHAR(30),
    -- result_updated
    -- board_started
    -- player_arrived
    -- observer_note

    payload JSONB,

    created_at TIMESTAMP DEFAULT now()
);
```

## Пример payload

```json
{
  "old_result": null,
  "new_result": "1-0"
}
```

---

# 8. tournament_standings — положение после каждого тура

Ключевая таблица для аналитики.

## Snapshot per round

```sql
CREATE TABLE tournament_standings (
    id BIGSERIAL PRIMARY KEY,

    tournament_id BIGINT NOT NULL
        REFERENCES tournaments(id),

    round_number INTEGER NOT NULL,

    player_id BIGINT NOT NULL
        REFERENCES players(id),

    position INTEGER,

    points NUMERIC(4,2),

    buchholz NUMERIC(6,2),
    buchholz_cut1 NUMERIC(6,2),
    sonneborn_berger NUMERIC(6,2),

    wins INTEGER,
    draws INTEGER,
    losses INTEGER,

    rating_delta INTEGER,

    performance_rating INTEGER,

    created_at TIMESTAMP DEFAULT now(),

    UNIQUE(tournament_id, round_number, player_id)
);
```

---

# Почему standings отдельной таблицей

Это позволяет:

* показывать таблицу после любого тура;
* строить динамику мест;
* делать replay турнира;
* быстро показывать изменения.

---

# 9. player_opponent_stats — агрегированная статистика

Можно:

* либо materialized view;
* либо обновляемая таблица.

```sql
CREATE MATERIALIZED VIEW player_opponent_stats AS
SELECT
    g.white_player_id AS player_id,
    g.black_player_id AS opponent_id,

    COUNT(*) AS games_count,

    SUM(CASE WHEN g.result = '1-0' THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN g.result = '0-1' THEN 1 ELSE 0 END) AS losses,
    SUM(CASE WHEN g.result = '1/2-1/2' THEN 1 ELSE 0 END) AS draws

FROM games g
GROUP BY 1,2;
```

---

# 10. player_tournament_summary

Витрина для карточки игрока.

```sql
CREATE MATERIALIZED VIEW player_tournament_summary AS
SELECT
    tp.player_id,
    tp.tournament_id,

    MAX(ts.round_number) AS rounds_played,
    MAX(ts.points) AS final_points,
    MAX(ts.position) FILTER (
        WHERE ts.round_number = t.rounds_count
    ) AS final_position,

    MAX(ts.rating_delta) AS rating_delta

FROM tournament_players tp
JOIN tournaments t ON t.id = tp.tournament_id
JOIN tournament_standings ts
    ON ts.tournament_id = tp.tournament_id
   AND ts.player_id = tp.player_id

GROUP BY 1,2;
```

---

# 11. live_predictions — прогнозы

Расчёты делает внешний сервис.

```sql
CREATE TABLE live_predictions (
    id BIGSERIAL PRIMARY KEY,

    tournament_id BIGINT NOT NULL
        REFERENCES tournaments(id),

    round_number INTEGER NOT NULL,

    player_id BIGINT NOT NULL
        REFERENCES players(id),

    prediction_type VARCHAR(30),
    -- finish_position
    -- rating_delta
    -- podium_probability

    payload JSONB NOT NULL,

    created_at TIMESTAMP DEFAULT now()
);
```

## Пример payload

```json
{
  "predicted_position": 3,
  "probability_top3": 0.72,
  "expected_points": 6.5
}
```

---

# 12. what_if_scenarios

Для пользовательских прогнозов.

```sql
CREATE TABLE what_if_scenarios (
    id BIGSERIAL PRIMARY KEY,

    tournament_id BIGINT NOT NULL,

    player_id BIGINT NOT NULL,

    round_number INTEGER NOT NULL,

    assumed_result VARCHAR(10),

    payload JSONB,

    created_at TIMESTAMP DEFAULT now()
);
```

---

# 13. observer_notes — живые заметки болельщиков

Это даёт ощущение присутствия.

```sql
CREATE TABLE observer_notes (
    id BIGSERIAL PRIMARY KEY,

    tournament_id BIGINT NOT NULL
        REFERENCES tournaments(id),

    round_number INTEGER,

    player_id BIGINT
        REFERENCES players(id),

    author_name TEXT,

    note_text TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT now()
);
```

## Примеры

* «Играл очень быстро первые 15 ходов»
* «После партии обсуждал ничью с тренером»
* «Похоже, готовил вариант против Сицилианки»

---

# 14. notifications — подписки и уведомления

Для вовлечения болельщиков.

```sql
CREATE TABLE notification_subscriptions (
    id BIGSERIAL PRIMARY KEY,

    user_external_id TEXT,

    player_id BIGINT REFERENCES players(id),

    tournament_id BIGINT REFERENCES tournaments(id),

    notify_round_results BOOLEAN DEFAULT TRUE,
    notify_rating_changes BOOLEAN DEFAULT TRUE,
    notify_pairings BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT now()
);
```

---

# 15. ingestion_logs — журнал загрузки данных

Критически важно.

```sql
CREATE TABLE ingestion_logs (
    id BIGSERIAL PRIMARY KEY,

    source_name VARCHAR(50),

    entity_type VARCHAR(50),

    entity_external_id TEXT,

    status VARCHAR(20),

    message TEXT,

    created_at TIMESTAMP DEFAULT now()
);
```

---

# Важные представления

---

# v_player_profile

Карточка шахматиста.

```sql
CREATE VIEW v_player_profile AS
SELECT
    p.id,
    p.full_name,

    r.rating_value AS current_rating,

    COUNT(DISTINCT tp.tournament_id) AS tournaments_played,
    COUNT(g.id) AS games_played

FROM players p
LEFT JOIN player_ratings r
    ON r.player_id = p.id
   AND r.valid_to IS NULL

LEFT JOIN tournament_players tp
    ON tp.player_id = p.id

LEFT JOIN games g
    ON g.white_player_id = p.id
    OR g.black_player_id = p.id

GROUP BY 1,2,3;
```

---

# v_active_tournament_table

Текущая таблица турнира.

```sql
CREATE VIEW v_active_tournament_table AS
SELECT *
FROM tournament_standings ts
JOIN tournaments t
  ON t.id = ts.tournament_id
WHERE t.is_active = TRUE;
```

---

# Оптимизация

---

# Индексы

Обязательно:

```sql
CREATE INDEX idx_games_white_player
ON games(white_player_id);

CREATE INDEX idx_games_black_player
ON games(black_player_id);

CREATE INDEX idx_games_round
ON games(round_id);

CREATE INDEX idx_standings_tournament_round
ON tournament_standings(tournament_id, round_number);

CREATE INDEX idx_ratings_player_period
ON player_ratings(player_id, valid_from, valid_to);
```

---

# Партиционирование

Если проект вырастет:

* `games` по году;
* `game_events` по месяцу;
* `tournament_standings` по турниру.

---

# Как выглядит поток данных

## 1. Парсер chess-results

Обновляет:

* турниры;
* туры;
* pairings;
* результаты партий;
* standings.

## 2. Парсер ФШР

Обновляет:

* player_ratings.

## 3. Аналитический сервис

Считает:

* прогнозы;
* performance;
* вероятность мест.

## 4. Notification service

Рассылает:

* «тур завершён»;
* «рейтинг изменился»;
* «изменилось место после тура».

---

# Что особенно важно именно для шахмат

## 1. Snapshot standings

Без них невозможно:

* история позиций;
* replay турнира;
* live-анимация изменения мест.

---

## 2. История рейтингов

Иначе нельзя:

* строить графики;
* анализировать прогресс;
* считать performance относительно рейтинга на момент турнира.

---

## 3. Separate tournament participation

Игрок ≠ участие в турнире.

Один и тот же игрок:

* имеет разный стартовый рейтинг;
* титул;
* стартовый номер.

---

# Рекомендуемый стек вокруг БД

## ingestion

* Python
* BeautifulSoup
* Playwright (если нужна динамика)

## API

* FastAPI / NestJS

## realtime

* PostgreSQL LISTEN/NOTIFY
  или
* Kafka/RabbitMQ

## аналитика

* ClickHouse (если проект вырастет)

---

# Минимально жизнеспособное ядро (MVP)

Для старта достаточно:

## Таблицы

* players
* player_ratings
* tournaments
* tournament_rounds
* tournament_players
* games
* tournament_standings

## Views

* v_player_profile
* v_active_tournament_table

Этого уже хватит для:

* профилей;
* live-таблиц;
* динамики рейтингов;
* статистики соперников;
* мониторинга турниров.
