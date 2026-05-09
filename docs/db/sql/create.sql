-- ============================================
-- Chessfan MVP Database Schema
-- PostgreSQL 13+
-- ============================================

-- 1. Таблица игроков
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    rus_id INTEGER UNIQUE,
    name VARCHAR(200) NOT NULL,
    gender CHAR(1) NOT NULL CHECK (gender IN ('M', 'F')),
    birth_year SMALLINT,
    city VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE players IS 'Базовая информация о шахматистах';
COMMENT ON COLUMN players.rus_id IS 'ID игрока в российской федерации';
COMMENT ON COLUMN players.city IS 'Город проживания';

-- 2. Таблица турниров
CREATE TABLE tournaments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(300) NOT NULL,
    location VARCHAR(200),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tournaments IS 'Метаданные турниров';

-- 3. Участие игроков в турнирах
CREATE TABLE tournament_players (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    rating_at_tournament SMALLINT NOT NULL,
    title VARCHAR(20),
    seed SMALLINT,
    UNIQUE (tournament_id, player_id)
);

COMMENT ON TABLE tournament_players IS 'Участие игроков в турнирах';
COMMENT ON COLUMN tournament_players.rating_at_tournament IS 'Рейтинг игрока на момент турнира';

-- 4. Партии
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    round SMALLINT NOT NULL DEFAULT 1,
    white_player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    black_player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    score DECIMAL(3,1) NOT NULL CHECK (score IN (0, 0.5, 1)),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (white_player_id != black_player_id)
);

COMMENT ON TABLE games IS 'Результаты партий';
COMMENT ON COLUMN games.score IS 'Очки белых (1 - победа, 0.5 - ничья, 0 - поражение)';

-- 5. История рейтингов
CREATE TABLE player_ratings (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL,
    rating_date DATE NOT NULL,
    source_tournament_id INTEGER REFERENCES tournaments(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE player_ratings IS 'История рейтингов игроков';
COMMENT ON COLUMN player_ratings.rating_date IS 'Дата, на которую действует рейтинг';

-- 6. Турнирная таблица (снимки)
CREATE TABLE tournament_standings (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    round_number SMALLINT NOT NULL,
    points DECIMAL(4,1) NOT NULL,
    position SMALLINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tournament_id, player_id, round_number)
);

COMMENT ON TABLE tournament_standings IS 'Снимки турнирной таблицы после каждого тура';

-- ============================================
-- Индексы
-- ============================================

CREATE INDEX idx_tournament_players_tournament ON tournament_players(tournament_id);
CREATE INDEX idx_tournament_players_player ON tournament_players(player_id);
CREATE INDEX idx_games_tournament ON games(tournament_id);
CREATE INDEX idx_games_round ON games(tournament_id, round);
CREATE INDEX idx_games_white ON games(white_player_id);
CREATE INDEX idx_games_black ON games(black_player_id);
CREATE INDEX idx_player_ratings_player ON player_ratings(player_id);
CREATE INDEX idx_player_ratings_date ON player_ratings(player_id, rating_date);
CREATE INDEX idx_tournament_standings_tournament ON tournament_standings(tournament_id);
CREATE INDEX idx_tournament_standings_round ON tournament_standings(tournament_id, round_number);
CREATE INDEX idx_tournaments_dates ON tournaments(start_date, end_date);

-- ============================================
-- Представления (Views)
-- ============================================

-- Текущая турнирная таблица
CREATE VIEW v_active_tournament_table AS
SELECT 
    t.id AS tournament_id,
    t.name AS tournament_name,
    t.start_date,
    t.end_date,
    ts.player_id,
    p.name AS player_name,
    ts.points,
    ts.position,
    ts.round_number
FROM tournament_standings ts
JOIN tournaments t ON ts.tournament_id = t.id
JOIN players p ON ts.player_id = p.id
WHERE ts.round_number = (
    SELECT MAX(round_number) 
    FROM tournament_standings ts2 
    WHERE ts2.tournament_id = ts.tournament_id
)
ORDER BY t.id, ts.position;

-- Карточка игрока
CREATE VIEW v_player_profile AS
SELECT 
    p.id AS player_id,
    p.name AS player_name,
    p.gender,
    p.birth_year,
    p.city,
    p.rus_id,
    MAX(pr.rating) AS current_rating,
    COUNT(DISTINCT tp.tournament_id) AS tournaments_played,
    COUNT(g.id) AS games_played,
    COALESCE(SUM(CASE WHEN g.white_player_id = p.id AND g.score = 1 THEN 1 ELSE 0 END), 0) +
    COALESCE(SUM(CASE WHEN g.black_player_id = p.id AND g.score = 0 THEN 1 ELSE 0 END), 0) AS wins,
    COALESCE(SUM(CASE WHEN (g.white_player_id = p.id OR g.black_player_id = p.id) AND g.score = 0.5 THEN 1 ELSE 0 END), 0) AS draws,
    COALESCE(SUM(CASE WHEN g.white_player_id = p.id AND g.score = 0 THEN 1 ELSE 0 END) +
             SUM(CASE WHEN g.black_player_id = p.id AND g.score = 1 THEN 1 ELSE 0 END), 0) AS losses
FROM players p
LEFT JOIN tournament_players tp ON p.id = tp.player_id
LEFT JOIN games g ON p.id IN (g.white_player_id, g.black_player_id)
LEFT JOIN player_ratings pr ON p.id = pr.player_id
GROUP BY p.id, p.name, p.gender, p.birth_year, p.city, p.rus_id;

-- История рейтингов
CREATE VIEW v_player_rating_history AS
SELECT 
    p.id AS player_id,
    p.name AS player_name,
    pr.rating,
    pr.rating_date,
    t.name AS tournament_name
FROM player_ratings pr
JOIN players p ON pr.player_id = p.id
LEFT JOIN tournaments t ON pr.source_tournament_id = t.id
ORDER BY p.id, pr.rating_date;

-- ============================================
-- pg_notify — Live-уведомления
-- ============================================

-- Функция для уведомлений
CREATE OR REPLACE FUNCTION notify_game_result_change()
RETURNS TRIGGER AS $$
DECLARE
    notification JSONB;
    tournament_name VARCHAR(300);
    round_num SMALLINT;
BEGIN
    SELECT name, COALESCE(NEW.round, 1) 
    INTO tournament_name, round_num
    FROM tournaments 
    WHERE id = NEW.tournament_id;
    
    notification = jsonb_build_object(
        'event', CASE 
            WHEN TG_OP = 'INSERT' THEN 'game_created'
            WHEN TG_OP = 'UPDATE' THEN 'game_updated'
            WHEN TG_OP = 'DELETE' THEN 'game_deleted'
        END,
        'game_id', COALESCE(NEW.id, OLD.id),
        'tournament_id', COALESCE(NEW.tournament_id, OLD.tournament_id),
        'tournament_name', tournament_name,
        'round', round_num,
        'white_player_id', COALESCE(NEW.white_player_id, OLD.white_player_id),
        'black_player_id', COALESCE(NEW.black_player_id, OLD.black_player_id),
        'score', COALESCE(NEW.score, OLD.score),
        'timestamp', NOW()
    );
    
    PERFORM pg_notify('game_result_changes', notification::text);
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Триггер
DROP TRIGGER IF EXISTS trg_notify_game_result_change ON games;
CREATE TRIGGER trg_notify_game_result_change
AFTER INSERT OR UPDATE OR DELETE ON games
FOR EACH ROW
EXECUTE FUNCTION notify_game_result_change();