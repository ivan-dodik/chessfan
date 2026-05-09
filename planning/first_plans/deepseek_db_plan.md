Отличная задача! Как фанат, я хочу видеть не только сухие цифры, но и тренды, «живые» прогнозы и моментальные оповещения. Ниже — проект БД под PostgreSQL, учитывающий специфику офлайн-турниров, задержки обновлений (только после тура) и потребность в «what-if» анализах.

## 1. Принципы организации БД

- **Историчность**: рейтинг меняется только после турнира → храним снимки рейтинга на момент каждого турнира и отдельно историю изменений.
- **Контроллер обновлений**: внешние программы пишут данные пакетно (например, после каждого тура). Для избежания гонок используем `upsert` (ON CONFLICT) и версионирование.
- **Поддержка «что-если»**: выделяем отдельную схему для витрин/материализованных представлений, где можно быстро агрегировать.
- **Уведомления**: используем триггеры + `pg_notify` для отправки событий болельщикам через бекенд.

## 2. Схема базы данных (основные таблицы)

### 2.1. Справочники

```sql
-- Шахматисты (уникальная информация)
CREATE TABLE chess.player (
    player_id      SERIAL PRIMARY KEY,
    fide_id        INTEGER UNIQUE,         -- ID FIDE (если есть)
    rus_id         INTEGER UNIQUE,         -- ID Федерации России
    first_name     TEXT NOT NULL,
    last_name      TEXT NOT NULL,
    birth_date     DATE,
    sex            CHAR(1) CHECK (sex IN ('M','F')),
    city           TEXT,
    federation     TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Турниры
CREATE TABLE tournament (
    tournament_id   SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    federation      TEXT,
    city            TEXT,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    time_control    TEXT,                  -- например, "90+30"
    rounds_total    SMALLINT NOT NULL,
    source_url      TEXT,                  -- ссылка chess-results
    is_active       BOOLEAN DEFAULT TRUE
);
```

### 2.2. Участие и рейтинги

```sql
-- Участие шахматиста в турнире (данные до начала)
CREATE TABLE tournament_registration (
    reg_id            SERIAL PRIMARY KEY,
    player_id         INTEGER REFERENCES chess.player(player_id),
    tournament_id     INTEGER REFERENCES tournament(tournament_id),
    rating_before     NUMERIC(6,1) NOT NULL,   -- рейтинг на момент начала турнира
    rating_change     NUMERIC(6,1),            -- заполнится после турнира
    final_position    SMALLINT,
    total_points      NUMERIC(4,2),            -- 0..rounds_total*1
    is_finished       BOOLEAN DEFAULT FALSE,
    UNIQUE (player_id, tournament_id)
);

-- История изменения рейтинга вне турниров (если нужно по месяцам/дням)
CREATE TABLE player_rating_history (
    history_id    SERIAL PRIMARY KEY,
    player_id     INTEGER REFERENCES chess.player(player_id),
    recorded_at   DATE NOT NULL,              -- обычно дата окончания турнира
    rating        NUMERIC(6,1) NOT NULL,
    reason        TEXT,                       -- "после турнира X" или "ежемесячное изменение"
    UNIQUE (player_id, recorded_at)
);
```

### 2.3. Игры (партии)

```sql
-- Партия (одна игра между двумя игроками)
CREATE TABLE game (
    game_id           SERIAL PRIMARY KEY,
    tournament_id     INTEGER REFERENCES tournament(tournament_id),
    round_num         SMALLINT NOT NULL,
    board_num         SMALLINT,                -- доска
    player_white_id   INTEGER REFERENCES chess.player(player_id),
    player_black_id   INTEGER REFERENCES chess.player(player_id),
    result            CHAR(1) CHECK (result IN ('1','0','=')),  -- 1 – белые выиграли, 0 – чёрные, = – ничья
    pgn               TEXT,                    -- полная нотация (опционально)
    is_rated          BOOLEAN DEFAULT TRUE,
    last_update       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tournament_id, round_num, board_num)
);

-- Индивидуальная партия с очками для каждого игрока (денормализация для скорости)
CREATE TABLE player_game_score (
    score_id      SERIAL PRIMARY KEY,
    game_id       INTEGER REFERENCES game(game_id) ON DELETE CASCADE,
    player_id     INTEGER REFERENCES chess.player(player_id),
    points        NUMERIC(3,2) NOT NULL,     -- 1, 0.5, 0
    color         CHAR(1) CHECK (color IN ('W','B')),
    opponent_id   INTEGER REFERENCES chess.player(player_id),
    UNIQUE (game_id, player_id)
);
```

### 2.4. Для активного турнира и прогнозов

```sql
-- Снимок состояния после каждого тура (витрина для быстрых запросов)
CREATE MATERIALIZED VIEW tournament_standings AS
WITH round_points AS (
    SELECT 
        pgs.player_id,
        t.tournament_id,
        t.round_num,
        SUM(pgs.points) OVER (PARTITION BY pgs.player_id, t.tournament_id ORDER BY t.round_num) AS cum_points
    FROM player_game_score pgs
    JOIN game g ON pgs.game_id = g.game_id
    JOIN tournament t ON g.tournament_id = t.tournament_id
)
SELECT 
    tournament_id,
    player_id,
    round_num,
    cum_points,
    RANK() OVER (PARTITION BY tournament_id, round_num ORDER BY cum_points DESC) AS position
FROM round_points;

-- Таблица для кэширования "what-if" сценариев (создаётся по запросу болельщика)
CREATE TABLE whatif_scenario (
    scenario_id   SERIAL PRIMARY KEY,
    player_id     INTEGER,
    tournament_id INTEGER,
    round_num     SMALLINT,
    assumed_result CHAR(1),    -- '1','0','='
    predicted_points NUMERIC(4,2),
    predicted_position SMALLINT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    ttl           INTERVAL DEFAULT '1 hour'
);
```

## 3. Индексы для производительности

```sql
-- Основные запросы
CREATE INDEX idx_game_tournament_round ON game(tournament_id, round_num);
CREATE INDEX idx_player_game_score_player ON player_game_score(player_id);
CREATE INDEX idx_tournament_registration_rating ON tournament_registration(rating_before);
CREATE INDEX idx_rating_history_player_date ON player_rating_history(player_id, recorded_at);
CREATE INDEX idx_tournament_active ON tournament(is_active) WHERE is_active = true;
CREATE INDEX idx_player_name_trgm ON chess.player USING gin (last_name gin_trgm_ops);
```

## 4. Представления (views) для типовых запросов

### 4.1. Анкета шахматиста со сводкой

```sql
CREATE VIEW player_profile AS
SELECT 
    p.player_id, p.first_name, p.last_name, p.birth_date, p.city,
    ph.rating AS current_rating,
    (SELECT COUNT(*) FROM tournament_registration tr WHERE tr.player_id = p.player_id) AS tournaments_played,
    (SELECT COUNT(*) FROM player_game_score pgs WHERE pgs.player_id = p.player_id) AS games_played
FROM chess.player p
LEFT JOIN LATERAL (
    SELECT rating FROM player_rating_history 
    WHERE player_id = p.player_id 
    ORDER BY recorded_at DESC LIMIT 1
) ph ON true;
```

### 4.2. Динамика рейтинга во времени

```sql
CREATE VIEW rating_timeline AS
SELECT 
    prh.player_id,
    prh.recorded_at,
    prh.rating,
    t.name AS tournament_name,
    tr.final_position
FROM player_rating_history prh
LEFT JOIN tournament_registration tr ON prh.player_id = tr.player_id AND prh.recorded_at BETWEEN (SELECT start_date FROM tournament WHERE tournament_id = tr.tournament_id) AND (SELECT end_date FROM tournament WHERE tournament_id = tr.tournament_id)
LEFT JOIN tournament t ON tr.tournament_id = t.tournament_id
ORDER BY prh.player_id, prh.recorded_at;
```

### 4.3. Статистика игр с конкретным соперником

```sql
CREATE VIEW h2h_stats AS
SELECT 
    p1.player_id AS player_a,
    p2.player_id AS player_b,
    COUNT(*) AS games_count,
    SUM(CASE WHEN (pgs.color = 'W' AND g.result = '1') OR (pgs.color = 'B' AND g.result = '0') THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN g.result = '=' THEN 1 ELSE 0 END) AS draws,
    SUM(CASE WHEN (pgs.color = 'W' AND g.result = '0') OR (pgs.color = 'B' AND g.result = '1') THEN 1 ELSE 0 END) AS losses
FROM player_game_score pgs
JOIN game g ON pgs.game_id = g.game_id
JOIN player_game_score pgs2 ON g.game_id = pgs2.game_id AND pgs2.player_id != pgs.player_id
JOIN chess.player p1 ON pgs.player_id = p1.player_id
JOIN chess.player p2 ON pgs2.player_id = p2.player_id
GROUP BY p1.player_id, p2.player_id;
```

## 5. Механизм оповещений (для живых болельщиков)

```sql
-- Функция, которая триггерится при обновлении результатов партии
CREATE OR REPLACE FUNCTION notify_game_update()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'game_result_changed',
        json_build_object(
            'tournament_id', NEW.tournament_id,
            'round', NEW.round_num,
            'board', NEW.board_num,
            'result', NEW.result,
            'last_update', NEW.last_update
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER game_update_trigger
AFTER INSERT OR UPDATE OF result ON game
FOR EACH ROW EXECUTE FUNCTION notify_game_update();
```

Бекенд подписывается на канал `game_result_changed` и шлёт push-уведомления болельщикам.

## 6. Рекомендации по обновлению внешними программами

1. **Парсинг chess-results.com после каждого тура**:
   - Пишем `player`, `tournament` (если новый) → `game` + `player_game_score`.
   - После завершения турнира: подсчитываем `rating_change` в `tournament_registration` и вставляем запись в `player_rating_history`.

2. **Загрузка рейтингов с сайта РФ**:
   - Ежедневно/еженедельно скрипт подтягивает ID `rus_id` и обновляет `player_rating_history` (reason = 'ежемесячный рейтинг РФ').

3. **Обновление `tournament_standings`**:
   - Материализованное представление можно обновлять `REFRESH MATERIALIZED VIEW CONCURRENTLY` после каждого тура (требует уникального индекса).

## 7. Пример сложного «what-if» запроса (без хранения)

```sql
-- Прогноз: если игрок N в туре M наберёт X очков, какое место займёт?
WITH current AS (
    SELECT player_id, cum_points 
    FROM tournament_standings 
    WHERE tournament_id = 123 AND round_num = 2
),
hypothetical AS (
    SELECT 
        player_id,
        cum_points + CASE 
            WHEN player_id = 42 THEN 1.0   -- допустим, победит
            ELSE 0 
        END AS new_points
    FROM current
)
SELECT 
    player_id,
    new_points,
    RANK() OVER (ORDER BY new_points DESC) AS predicted_place
FROM hypothetical;
```

---

## Итог: что даёт такая БД болельщику?

- ✅ Анкету и динамику рейтинга (с графиками по турам/турнирам).
- ✅ Статистику конкретных соперников (классический H2H).
- ✅ Очки, позицию и прогноз после каждого тура (через материализованное представление).
- ✅ «Что-если» за секунды (без пересчёта всей истории).
- ✅ Лайв-оповещения прямо в мессенджер/приложение (через pg_notify).

Если нужно, добавлю схему партиционирования для `player_game_score` (по годам) и подробный пример ETL-скрипта для парсинга.
