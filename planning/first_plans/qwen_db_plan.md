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