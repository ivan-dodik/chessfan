# Проектирование

Цель: собрать идеи для проекта по мониторингу игры шахматиста.

## Первоначальный сбор идей

Промпт:

```
РОЛЬ: ты шахматный болельщик которому хочется отслеживать игру любимых шахматистов на офлайн турнирах, мониторить их изменения рейтинга, статистику игр, получать оповещения о результатах

ЦЕЛЬ: разработка сервиса статистики и мониторинга игры шахматиста

ЗАДАЧА: спроектируй базу данных для сбора и хранения информации о шахматистах и турнирах.

ТРЕБОВАНИЯ:
 * БД: PostgreSQL
 * внесение новых записей и обновление существующих будет осуществляться внешними программами
 * расчёт статистики будет осуществляться внешними программами за исключением простой выборки и агрегации, для построения которых могут использоваться представления и витрины данных

ИСТОЧНИКИ ДАННЫХ: сайт chess-results.com с информацией о прошедших турнирах и активном турнире с турами и результатами, индивидуальный рейтинг шахматистов на сайте шахматной федерации России.

ОГРАНИЧЕНИЯ: соревнования проводятся оффлайн, с обновлением информации о результатах партий на chess-results после каждого тура. Рейтинг шахматистов пересчитывается только после завершения турнира.

ДОПОЛНЕНИЕ:
 * ты можешь вживую общаться с шахматистами в перерывах между турами турнира;
 * твои коллеги болельщики, которые не могут придти поболеть вживую, хотели бы оперативно получать всю информацию и быть также вовлечены в игру, как и ты.


ТИПИЧНЫЕ ЗАПРОСЫ

Общая статистика:
 * просмотр анкеты шахматиста
 * просмотр динамики изменения рейтинга со временем
 * просмотр сыгранных турниров со статистикой по очкам, занятым местам и изменениям рейтинга по итогу турнира
 * просмотр сведений о турнире: количество игроков (в том числе их рейтинг, пол, возраст), туров, средний рейтинг турнира
 * статистика игр с соперником

Просмотр активного турнира:
 * просмотр очков по турам
 * просмотр позиции в каждом туре
 * прогноз изменения позиции после каждого обновления результатов партий в туре
 * прогноз "что-если" (если шахматист в туре сыграет так, то какое место займёт после его завершения)

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
 * предложения по организации БД
 * список таблиц с полями и ключами

### DeepSeek

```
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
```

### Qwen

```
# Проектирование базы данных для сервиса мониторинга шахматистов

## 🏗️ Архитектурные принципы

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Источники данных│────▶│   PostgreSQL    │────▶│  Внешние сервисы│
│  • chess-results│ ETL │   (OLTP +       │ API │  • Статистика  │
│  • РШФ/РШФ сайт │     │   Analytics)    │     │  • Уведомления │
│  • ручной ввод  │     │                 │     │  • Frontend    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Views &        │
                    │  Materialized   │
                    │  Views для      │
                    │  агрегаций      │
                    └─────────────────┘
```

**Ключевые решения:**
- Нормализованная схема 3НФ для транзакционных данных
- Представления (VIEW) и материализованные представления (MATERIALIZED VIEW) для аналитики
- Внешние программы обновляют данные через `INSERT/UPDATE`, БД не считает сложный Elo
- Индексы под типовые запросы + `pg_cron` для автообновления витрин

---

## 📋 Схема таблиц

### 1. `players` — Шахматисты
```sql
CREATE TABLE players (
    player_id           BIGSERIAL PRIMARY KEY,
    fide_id             INTEGER UNIQUE,                    -- ID в базе FIDE
    rcf_id              VARCHAR(50) UNIQUE,                -- ID в базе РШФ
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    patronymic          VARCHAR(100),                      -- Отчество (для РШФ)
    birth_date          DATE,
    gender              CHAR(1) CHECK (gender IN ('M', 'F')),
    country_code        CHAR(3) DEFAULT 'RUS',             -- ISO 3166-1 alpha-3
    title               VARCHAR(5) CHECK (title IN ('GM', 'IM', 'FM', 'WGM', 'WIM', 'WFM', 'CM', 'WCM', None)),
    photo_url           TEXT,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE (last_name, first_name, birth_date)             -- Защита от дублей
);

CREATE INDEX idx_players_name ON players (last_name, first_name);
CREATE INDEX idx_players_fide ON players (fide_id) WHERE fide_id IS NOT NULL;
CREATE INDEX idx_players_rcf ON players (rcf_id) WHERE rcf_id IS NOT NULL;
```

### 2. `ratings` — История рейтингов
```sql
CREATE TABLE ratings (
    rating_id           BIGSERIAL PRIMARY KEY,
    player_id           BIGINT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    rating_type         VARCHAR(10) NOT NULL CHECK (rating_type IN ('classical', 'rapid', 'blitz')),
    rating_value        SMALLINT NOT NULL CHECK (rating_value BETWEEN 0 AND 3000),
    games_count         INTEGER,                           -- Количество сыгранных партий для рейтинга
    rating_date         DATE NOT NULL,                     -- Дата публикации рейтинга
    source              VARCHAR(10) CHECK (source IN ('fide', 'rcf')),
    tournament_id       BIGINT,                            -- Если рейтинг обновлён после турнира
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE (player_id, rating_type, rating_date, source)
);

CREATE INDEX idx_ratings_player_date ON ratings (player_id, rating_date DESC);
CREATE INDEX idx_ratings_current ON ratings (rating_type, rating_date DESC) 
    WHERE rating_date = (SELECT MAX(rating_date) FROM ratings r2 WHERE r2.rating_type = ratings.rating_type);
```

### 3. `tournaments` — Турниры
```sql
CREATE TABLE tournaments (
    tournament_id       BIGSERIAL PRIMARY KEY,
    name                VARCHAR(255) NOT NULL,
    short_name          VARCHAR(100),                      -- "ЧР 2024", "Аэрофлот Опен"
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    location            VARCHAR(255),                      -- Город, место проведения
    country_code        CHAR(3) DEFAULT 'RUS',
    tournament_format   VARCHAR(20) CHECK (tournament_format IN ('swiss', 'round-robin', 'knockout', 'team')),
    time_control        VARCHAR(50),                       -- "90+30", "15+10"
    category            VARCHAR(20),                       -- "X", "XV", "open", "women"
    average_rating      SMALLINT,                          -- Средний рейтинг топ-10/всех
    total_rounds        SMALLINT NOT NULL CHECK (total_rounds > 0),
    chess_results_id    VARCHAR(100) UNIQUE,               -- ID на chess-results.com
    rcf_url             TEXT,                              -- Ссылка на страницу РШФ
    status              VARCHAR(15) DEFAULT 'upcoming' 
                        CHECK (status IN ('upcoming', 'active', 'completed', 'cancelled')),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tournaments_dates ON tournaments (start_date DESC, end_date DESC);
CREATE INDEX idx_tournaments_active ON tournaments (status) WHERE status = 'active';
CREATE INDEX idx_tournaments_cr_id ON tournaments (chess_results_id) WHERE chess_results_id IS NOT NULL;
```

### 4. `participations` — Участие игроков в турнирах
```sql
CREATE TABLE participations (
    participation_id    BIGSERIAL PRIMARY KEY,
    tournament_id       BIGINT NOT NULL REFERENCES tournaments(tournament_id) ON DELETE CASCADE,
    player_id           BIGINT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    seed_number         SMALLINT,                          -- Посев по рейтингу
    initial_rating      SMALLINT NOT NULL CHECK (initial_rating BETWEEN 0 AND 3000),
    final_rating        SMALLINT CHECK (final_rating BETWEEN 0 AND 3000),  -- Заполняется после турнира
    rating_change       SMALLINT,                          -- final_rating - initial_rating
    total_points        NUMERIC(4,2) CHECK (total_points >= 0),  -- Очки: 1, 0.5, 0
    final_place         INTEGER,                           -- Итоговое место (с учётом коэффициентов)
    performance_rating  SMALLINT CHECK (performance_rating BETWEEN 0 AND 3000), -- Тперф
    is_withdrawn        BOOLEAN DEFAULT FALSE,             -- Снялся с турнира
    withdrawal_round    SMALLINT,                          -- После какого тура снялся
    notes               TEXT,
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE (tournament_id, player_id)
);

CREATE INDEX idx_participations_tournament ON participations (tournament_id);
CREATE INDEX idx_participations_player ON participations (player_id);
CREATE INDEX idx_participations_rating_change ON participations (tournament_id, rating_change) 
    WHERE rating_change IS NOT NULL;
```

### 5. `rounds` — Туры турнира
```sql
CREATE TABLE rounds (
    round_id            BIGSERIAL PRIMARY KEY,
    tournament_id       BIGINT NOT NULL REFERENCES tournaments(tournament_id) ON DELETE CASCADE,
    round_number        SMALLINT NOT NULL CHECK (round_number > 0),
    scheduled_start     TIMESTAMPTZ,
    scheduled_end       TIMESTAMPTZ,
    actual_start        TIMESTAMPTZ,
    actual_end          TIMESTAMPTZ,
    status              VARCHAR(15) DEFAULT 'scheduled' 
                        CHECK (status IN ('scheduled', 'in_progress', 'completed', 'postponed')),
    chess_results_url   TEXT,                              -- Ссылка на конкретный тур
    
    UNIQUE (tournament_id, round_number)
);

CREATE INDEX idx_rounds_tournament ON rounds (tournament_id, round_number);
CREATE INDEX idx_rounds_active ON rounds (status) WHERE status IN ('in_progress', 'completed');
```

### 6. `games` — Сыгранные партии
```sql
CREATE TABLE games (
    game_id             BIGSERIAL PRIMARY KEY,
    tournament_id       BIGINT NOT NULL REFERENCES tournaments(tournament_id) ON DELETE CASCADE,
    round_id            BIGINT NOT NULL REFERENCES rounds(round_id) ON DELETE CASCADE,
    white_player_id     BIGINT NOT NULL REFERENCES players(player_id),
    black_player_id     BIGINT NOT NULL REFERENCES players(player_id),
    result              VARCHAR(5) CHECK (result IN ('1-0', '0-1', '1/2-1/2', '*')),  -- * = не сыграна
    result_code         CHAR(1) CHECK (result_code IN ('W', 'L', 'D', '-')),  -- Для игрока: победа/поражение/ничья/-
    points_white        NUMERIC(2,1) GENERATED ALWAYS AS (
        CASE result WHEN '1-0' THEN 1.0 WHEN '1/2-1/2' THEN 0.5 ELSE 0.0 END
    ) STORED,
    points_black        NUMERIC(2,1) GENERATED ALWAYS AS (
        CASE result WHEN '0-1' THEN 1.0 WHEN '1/2-1/2' THEN 0.5 ELSE 0.0 END
    ) STORED,
    pgn                 TEXT,                              -- Нотация партии
    eco_code            VARCHAR(5),                        -- A00-E99
    opening_name        VARCHAR(255),
    moves_count         SMALLINT,
    game_date           TIMESTAMPTZ,
    board_number        SMALLINT,                          -- Номер доски в туре
    status              VARCHAR(15) DEFAULT 'scheduled' 
                        CHECK (status IN ('scheduled', 'in_progress', 'completed', 'forfeit')),
    source_updated_at   TIMESTAMPTZ,                       -- Когда данные получены из chess-results
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CHECK (white_player_id != black_player_id),
    UNIQUE (tournament_id, round_id, white_player_id, black_player_id)
);

CREATE INDEX idx_games_round ON games (round_id);
CREATE INDEX idx_games_player_tournament ON games (tournament_id, white_player_id);
CREATE INDEX idx_games_player_tournament ON games (tournament_id, black_player_id);
CREATE INDEX idx_games_unplayed ON games (status) WHERE status = 'scheduled';
CREATE INDEX idx_games_recent ON games (game_date DESC) WHERE status = 'completed';
```

### 7. `player_round_progress` — Прогресс игрока по турам (для прогнозов)
```sql
CREATE TABLE player_round_progress (
    progress_id         BIGSERIAL PRIMARY KEY,
    participation_id    BIGINT NOT NULL REFERENCES participations(participation_id) ON DELETE CASCADE,
    round_id            BIGINT NOT NULL REFERENCES rounds(round_id) ON DELETE CASCADE,
    
    -- Состояние до тура
    points_before       NUMERIC(4,2) NOT NULL DEFAULT 0,
    position_before     INTEGER,
    
    -- Состояние после тура (обновляется по мере появления результатов)
    points_after        NUMERIC(4,2),
    position_after      INTEGER,
    
    -- Данные о партии в этом туре
    opponent_player_id  BIGINT REFERENCES players(player_id),
    opponent_color      CHAR(5) CHECK (opponent_color IN ('white', 'black')),
    game_result         CHAR(1) CHECK (game_result IN ('W', 'L', 'D', '-')),  -- С точки зрения игрока
    game_id             BIGINT REFERENCES games(game_id),
    
    -- Прогнозные поля (заполняются внешним сервисом)
    projected_final_place_min INTEGER,  -- Минимальное возможное место при оптимальном финише
    projected_final_place_max INTEGER,  -- Максимальное возможное место при провале
    last_calculated     TIMESTAMPTZ,
    
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE (participation_id, round_id)
);

CREATE INDEX idx_progress_round ON player_round_progress (round_id);
CREATE INDEX idx_progress_player ON player_round_progress (participation_id, round_id);
```

### 8. `head_to_head` — Материализованная статистика личных встреч
```sql
CREATE MATERIALIZED VIEW head_to_head_stats AS
SELECT 
    p1.player_id AS player1_id,
    p2.player_id AS player2_id,
    COUNT(*) AS total_games,
    SUM(CASE WHEN g.result = '1-0' AND g.white_player_id = p1.player_id THEN 1
             WHEN g.result = '0-1' AND g.black_player_id = p1.player_id THEN 1
             ELSE 0 END) AS p1_wins,
    SUM(CASE WHEN g.result = '0-1' AND g.white_player_id = p1.player_id THEN 1
             WHEN g.result = '1-0' AND g.black_player_id = p1.player_id THEN 1
             ELSE 0 END) AS p2_wins,
    SUM(CASE WHEN g.result = '1/2-1/2' THEN 1 ELSE 0 END) AS draws,
    SUM(CASE WHEN g.white_player_id = p1.player_id THEN 1.0 
             WHEN g.black_player_id = p1.player_id THEN 0.0 END) AS p1_points_white,
    AVG(EXTRACT(YEAR FROM AGE(g.game_date))) AS avg_years_between_games
FROM games g
JOIN players p1 ON p1.player_id IN (g.white_player_id, g.black_player_id)
JOIN players p2 ON p2.player_id IN (g.white_player_id, g.black_player_id) 
    AND p1.player_id < p2.player_id  -- Чтобы не дублировать пары
WHERE g.status = 'completed'
GROUP BY p1.player_id, p2.player_id
HAVING COUNT(*) >= 1;

CREATE UNIQUE INDEX idx_h2h_pair ON head_to_head_stats (player1_id, player2_id);
CREATE INDEX idx_h2h_player1 ON head_to_head_stats (player1_id);
CREATE INDEX idx_h2h_player2 ON head_to_head_stats (player2_id);

-- Для обновления: REFRESH MATERIALIZED VIEW CONCURRENTLY head_to_head_stats;
```

---

## 🔍 Представления для типовых запросов

### Вью: `v_player_profile` — Анкета игрока с текущим рейтингом
```sql
CREATE VIEW v_player_profile AS
SELECT 
    p.player_id,
    p.fide_id,
    p.rcf_id,
    p.first_name,
    p.last_name,
    p.patronymic,
    p.birth_date,
    p.gender,
    p.country_code,
    p.title,
    p.photo_url,
    -- Текущие рейтинги (последние доступные)
    (SELECT rating_value FROM ratings r 
     WHERE r.player_id = p.player_id AND r.rating_type = 'classical' 
     ORDER BY r.rating_date DESC LIMIT 1) AS rating_classical,
    (SELECT rating_value FROM ratings r 
     WHERE r.player_id = p.player_id AND r.rating_type = 'rapid' 
     ORDER BY r.rating_date DESC LIMIT 1) AS rating_rapid,
    (SELECT rating_value FROM ratings r 
     WHERE r.player_id = p.player_id AND r.rating_type = 'blitz' 
     ORDER BY r.rating_date DESC LIMIT 1) AS rating_blitz,
    -- Статистика
    (SELECT COUNT(*) FROM participations WHERE player_id = p.player_id) AS tournaments_played,
    (SELECT COUNT(*) FROM games WHERE white_player_id = p.player_id OR black_player_id = p.player_id) AS total_games
FROM players p
WHERE p.is_active = TRUE;
```

### Вью: `v_rating_history` — Динамика рейтинга
```sql
CREATE VIEW v_rating_history AS
SELECT 
    r.player_id,
    r.rating_type,
    r.rating_value,
    r.rating_date,
    r.source,
    LAG(r.rating_value) OVER (PARTITION BY r.player_id, r.rating_type ORDER BY r.rating_date) AS prev_rating,
    r.rating_value - LAG(r.rating_value) OVER (PARTITION BY r.player_id, r.rating_type ORDER BY r.rating_date) AS rating_delta
FROM ratings r;
```

### Вью: `v_tournament_summary` — Сводка по турниру
```sql
CREATE VIEW v_tournament_summary AS
SELECT 
    t.tournament_id,
    t.name,
    t.start_date,
    t.end_date,
    t.location,
    t.tournament_format,
    t.total_rounds,
    t.status,
    COUNT(DISTINCT pa.player_id) AS total_players,
    COUNT(DISTINCT CASE WHEN p.gender = 'M' THEN pa.player_id END) AS male_players,
    COUNT(DISTINCT CASE WHEN p.gender = 'F' THEN pa.player_id END) AS female_players,
    AVG(pa.initial_rating) AS avg_rating,
    MIN(pa.initial_rating) AS min_rating,
    MAX(pa.initial_rating) AS max_rating,
    COUNT(DISTINCT CASE WHEN pa.final_place <= 3 THEN pa.player_id END) AS medalists_count
FROM tournaments t
LEFT JOIN participations pa ON pa.tournament_id = t.tournament_id
LEFT JOIN players p ON p.player_id = pa.player_id
GROUP BY t.tournament_id;
```

### Вью: `v_active_tournament_standings` — Текущая таблица активного турнира
```sql
CREATE VIEW v_active_tournament_standings AS
SELECT 
    pa.participation_id,
    pa.player_id,
    p.last_name,
    p.first_name,
    p.title,
    pa.initial_rating,
    pa.seed_number,
    COALESCE(prp.points_after, 0) AS current_points,
    prp.position_after AS current_position,
    -- Прогнозные поля
    prp.projected_final_place_min,
    prp.projected_final_place_max,
    -- Следующий соперник
    next_g.opponent_name,
    next_g.opponent_rating,
    next_g.color
FROM participations pa
JOIN players p ON p.player_id = pa.player_id
JOIN tournaments t ON t.tournament_id = pa.tournament_id
LEFT JOIN player_round_progress prp ON prp.participation_id = pa.participation_id 
    AND prp.round_id = (SELECT MAX(round_id) FROM rounds WHERE tournament_id = t.tournament_id AND status = 'completed')
LEFT JOIN LATERAL (
    SELECT 
        CASE 
            WHEN g.white_player_id = pa.player_id THEN p2.last_name || ' ' || p2.first_name
            ELSE p3.last_name || ' ' || p3.first_name
        END AS opponent_name,
        CASE 
            WHEN g.white_player_id = pa.player_id THEN pa2.initial_rating
            ELSE pa3.initial_rating
        END AS opponent_rating,
        CASE 
            WHEN g.white_player_id = pa.player_id THEN 'black'
            ELSE 'white'
        END AS color
    FROM games g
    LEFT JOIN players p2 ON p2.player_id = g.black_player_id
    LEFT JOIN players p3 ON p3.player_id = g.white_player_id
    LEFT JOIN participations pa2 ON pa2.player_id = g.black_player_id AND pa2.tournament_id = g.tournament_id
    LEFT JOIN participations pa3 ON pa3.player_id = g.white_player_id AND pa3.tournament_id = g.tournament_id
    WHERE g.tournament_id = t.tournament_id 
      AND g.round_id = (SELECT MIN(round_id) FROM rounds WHERE tournament_id = t.tournament_id AND status = 'scheduled')
      AND (g.white_player_id = pa.player_id OR g.black_player_id = pa.player_id)
    LIMIT 1
) next_g ON true
WHERE t.status = 'active'
ORDER BY current_points DESC, pa.seed_number;
```

---

## ⚙️ Технические рекомендации

### Индексы для производительности
```sql
-- Композитные индексы под частые фильтры
CREATE INDEX idx_games_player_round ON games (white_player_id, round_id) INCLUDE (result, status);
CREATE INDEX idx_games_player_round ON games (black_player_id, round_id) INCLUDE (result, status);

-- Частичные индексы для актуальных данных
CREATE INDEX idx_participations_active ON participations (tournament_id, final_place) 
    WHERE final_place IS NOT NULL;

-- GIN-индекс для полнотекстового поиска игроков
CREATE INDEX idx_players_search ON players USING GIN (
    to_tsvector('russian', last_name || ' ' || first_name || ' ' || COALESCE(patronymic, ''))
);
```

### Триггеры для поддержания целостности
```sql
-- Автоматическое обновление updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_players_updated BEFORE UPDATE ON players 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_tournaments_updated BEFORE UPDATE ON tournaments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Обновление материализованных представлений
```sql
-- Настроить pg_cron для автообновления каждые 15 минут во время активных турниров
SELECT cron.schedule('refresh-h2h', '*/15 * * * *', 
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY head_to_head_stats$$);

-- Или по событию: после вставки результатов тура
CREATE OR REPLACE FUNCTION refresh_stats_after_game_update()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status != 'completed' AND NEW.status = 'completed' THEN
        -- Асинхронно через LISTEN/NOTIFY или очередь задач
        PERFORM pg_notify('game_completed', NEW.game_id::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## 🔄 Интеграция с источниками данных

### Чеклист для внешних программ-загрузчиков:

| Источник | Частота | Что загружает | Ключевое поле для upsert |
|----------|---------|---------------|--------------------------|
| chess-results.com | После каждого тура | `tournaments`, `rounds`, `games`, `participations` | `chess_results_id` + `round_number` |
| РШФ (рейтинги) | Ежемесячно / после турниров | `ratings`, `players.rcf_id` | `player_id` + `rating_date` + `source` |
| Ручной ввод | По необходимости | `players.photo_url`, `notes`, `games.pgn` | `player_id` / `game_id` |

### Рекомендации по upsert:
```sql
-- Пример вставки/обновления партии
INSERT INTO games (tournament_id, round_id, white_player_id, black_player_id, result, ...)
VALUES (...)
ON CONFLICT (tournament_id, round_id, white_player_id, black_player_id)
DO UPDATE SET 
    result = EXCLUDED.result,
    status = EXCLUDED.status,
    pgn = COALESCE(EXCLUDED.pgn, games.pgn),  -- Не затирать, если нет новой нотации
    source_updated_at = EXCLUDED.source_updated_at,
    updated_at = NOW()
WHERE games.source_updated_at < EXCLUDED.source_updated_at;  -- Только если данные новее
```

---

## 📊 Поддержка "что-если" прогнозов

Для реализации прогнозных сценариев рекомендуется:

1. **Хранить "снимки" таблицы `player_round_progress`** перед каждым обновлением:
```sql
CREATE TABLE progress_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    round_id BIGINT NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    participation_id BIGINT,
    points_after NUMERIC(4,2),
    position_after INTEGER,
    -- ... остальные поля из player_round_progress
);
```

2. **Внешний сервис прогнозов** читает текущее состояние, симулирует результаты оставшихся туров (Монте-Карло / перебор) и записывает:
```sql
UPDATE player_round_progress 
SET 
    projected_final_place_min = 3,
    projected_final_place_max = 12,
    last_calculated = NOW()
WHERE participation_id = ? AND round_id = ?;
```

3. **Frontend** запрашивает прогноз через вью:
```sql
SELECT player_id, current_points, projected_final_place_min, projected_final_place_max
FROM v_active_tournament_standings
WHERE tournament_id = ?;
```

---

## 🗂️ Структура схемы (кратко)

```
players (1) ──< ratings (M)
    │
    └──< participations (M) >── tournaments (1)
                │                    │
                │                    └──< rounds (M)
                │                           │
                └──< player_round_progress (M) <── rounds
                │
                └──< games (M) >── players (через white/black)
                
head_to_head_stats (MATERIALIZED VIEW)
v_player_profile, v_rating_history, v_tournament_summary (VIEW)
```

---

## ✅ Чеклист готовности к продакшену

- [ ] Настроить `work_mem`, `shared_buffers` под аналитические запросы
- [ ] Включить `pg_stat_statements` для мониторинга медленных запросов
- [ ] Настроить репликацию (hot standby) для разделения OLTP/OLAP нагрузки
- [ ] Реализовать API-слой с пагинацией и кэшированием (Redis) для views
- [ ] Добавить аудит-лог изменений рейтингов и результатов (отдельная таблица `audit_log`)
- [ ] Протестировать `REFRESH MATERIALIZED VIEW CONCURRENTLY` под нагрузкой

Готов предоставить детальные миграции на Flyway/Liquibase или пример ETL-скрипта на Python для парсинга chess-results.com при необходимости. 🎯♟️
```

### ChatGPT

```
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
```
