-- ============================================
-- Chessfan Sample Data
-- For testing and development purposes
-- ============================================

-- ============================================
-- Sample Players (5 players)
-- ============================================

INSERT INTO players (rus_id, name, gender, birth_year, city) VALUES
(1001, 'Иванов Иван Иванович', 'M', 1990, 'Москва'),
(1002, 'Петров Петр Петрович', 'M', 1992, 'Санкт-Петербург'),
(1003, 'Сидорова Анна Сергеевна', 'F', 1995, 'Новосибирск'),
(1004, 'Смирнов Дмитрий Алексеевич', 'M', 1988, 'Екатеринбург'),
(1005, 'Кузнецова Елена Владимировна', 'F', 1993, 'Казань')
ON CONFLICT (rus_id) DO NOTHING;

-- ============================================
-- Sample Tournament
-- ============================================

INSERT INTO tournaments (name, location, start_date, end_date) VALUES
('Тестовый турнир по шахматам 2026', 'Москва', '2026-05-01', '2026-05-05')
ON CONFLICT ON CONSTRAINT tournaments_name_start_date_end_date_key DO NOTHING;

-- ============================================
-- Tournament Players (all 5 players participate)
-- ============================================

DO $$
DECLARE
    v_tournament_id INT;
    v_player1_id INT;
    v_player2_id INT;
    v_player3_id INT;
    v_player4_id INT;
    v_player5_id INT;
BEGIN
    SELECT id INTO v_tournament_id FROM tournaments WHERE name = 'Тестовый турнир по шахматам 2026';
    SELECT id INTO v_player1_id FROM players WHERE rus_id = 1001;
    SELECT id INTO v_player2_id FROM players WHERE rus_id = 1002;
    SELECT id INTO v_player3_id FROM players WHERE rus_id = 1003;
    SELECT id INTO v_player4_id FROM players WHERE rus_id = 1004;
    SELECT id INTO v_player5_id FROM players WHERE rus_id = 1005;
    
    INSERT INTO tournament_players (tournament_id, player_id, rating_at_tournament, title, seed) VALUES
    (v_tournament_id, v_player1_id, 2400, 'МС', 1),
    (v_tournament_id, v_player2_id, 2350, 'КМС', 2),
    (v_tournament_id, v_player3_id, 2200, NULL, 3),
    (v_tournament_id, v_player4_id, 2450, 'МС', 1),
    (v_tournament_id, v_player5_id, 2150, NULL, 5)
    ON CONFLICT (tournament_id, player_id) DO NOTHING;
END $$;

-- ============================================
-- Sample Games (for pg_notify testing)
-- ============================================

DO $$
DECLARE
    v_tournament_id INT;
    v_player1_id INT;
    v_player2_id INT;
    v_player3_id INT;
    v_player4_id INT;
    v_player5_id INT;
BEGIN
    SELECT id INTO v_tournament_id FROM tournaments WHERE name = 'Тестовый турнир по шахматам 2026';
    SELECT id INTO v_player1_id FROM players WHERE rus_id = 1001;
    SELECT id INTO v_player2_id FROM players WHERE rus_id = 1002;
    SELECT id INTO v_player3_id FROM players WHERE rus_id = 1003;
    SELECT id INTO v_player4_id FROM players WHERE rus_id = 1004;
    SELECT id INTO v_player5_id FROM players WHERE rus_id = 1005;
    
    -- Round 1 games
    INSERT INTO games (tournament_id, round, white_player_id, black_player_id, score) VALUES
    (v_tournament_id, 1, v_player1_id, v_player2_id, 1),    -- 1-0
    (v_tournament_id, 1, v_player3_id, v_player4_id, 0.5),  -- 1/2-1/2
    (v_tournament_id, 1, v_player5_id, v_player1_id, 0)     -- 0-1
    ON CONFLICT (tournament_id, round, white_player_id, black_player_id) DO NOTHING;
    
    -- Round 2 games
    INSERT INTO games (tournament_id, round, white_player_id, black_player_id, score) VALUES
    (v_tournament_id, 2, v_player2_id, v_player3_id, 1),    -- 1-0
    (v_tournament_id, 2, v_player4_id, v_player5_id, 0.5),  -- 1/2-1/2
    (v_tournament_id, 2, v_player1_id, v_player4_id, 1)     -- 1-0
    ON CONFLICT (tournament_id, round, white_player_id, black_player_id) DO NOTHING;
    
    -- Round 3 games
    INSERT INTO games (tournament_id, round, white_player_id, black_player_id, score) VALUES
    (v_tournament_id, 3, v_player3_id, v_player5_id, 1),    -- 1-0
    (v_tournament_id, 3, v_player1_id, v_player2_id, 0.5),  -- 1/2-1/2
    (v_tournament_id, 3, v_player4_id, v_player2_id, 0.5)   -- 1/2-1/2
    ON CONFLICT (tournament_id, round, white_player_id, black_player_id) DO NOTHING;
END $$;

-- ============================================
-- Sample Ratings History
-- ============================================

DO $$
DECLARE
    v_player1_id INT;
    v_player2_id INT;
    v_player3_id INT;
    v_player4_id INT;
    v_player5_id INT;
    v_tournament_id INT;
BEGIN
    SELECT id INTO v_player1_id FROM players WHERE rus_id = 1001;
    SELECT id INTO v_player2_id FROM players WHERE rus_id = 1002;
    SELECT id INTO v_player3_id FROM players WHERE rus_id = 1003;
    SELECT id INTO v_player4_id FROM players WHERE rus_id = 1004;
    SELECT id INTO v_player5_id FROM players WHERE rus_id = 1005;
    SELECT id INTO v_tournament_id FROM tournaments WHERE name = 'Тестовый турнир по шахматам 2026';
    
    -- Player 1 rating history
    INSERT INTO player_ratings (player_id, rating, rating_date, source_tournament_id) VALUES
    (v_player1_id, 2380, '2026-04-01', NULL),
    (v_player1_id, 2400, '2026-05-01', v_tournament_id)
    ON CONFLICT (player_id, rating_date) DO NOTHING;
    
    -- Player 2 rating history
    INSERT INTO player_ratings (player_id, rating, rating_date, source_tournament_id) VALUES
    (v_player2_id, 2330, '2026-04-01', NULL),
    (v_player2_id, 2350, '2026-05-01', v_tournament_id)
    ON CONFLICT (player_id, rating_date) DO NOTHING;
    
    -- Player 3 rating history
    INSERT INTO player_ratings (player_id, rating, rating_date, source_tournament_id) VALUES
    (v_player3_id, 2180, '2026-04-01', NULL),
    (v_player3_id, 2200, '2026-05-01', v_tournament_id)
    ON CONFLICT (player_id, rating_date) DO NOTHING;
    
    -- Player 4 rating history
    INSERT INTO player_ratings (player_id, rating, rating_date, source_tournament_id) VALUES
    (v_player4_id, 2430, '2026-04-01', NULL),
    (v_player4_id, 2450, '2026-05-01', v_tournament_id)
    ON CONFLICT (player_id, rating_date) DO NOTHING;
    
    -- Player 5 rating history
    INSERT INTO player_ratings (player_id, rating, rating_date, source_tournament_id) VALUES
    (v_player5_id, 2130, '2026-04-01', NULL),
    (v_player5_id, 2150, '2026-05-01', v_tournament_id)
    ON CONFLICT (player_id, rating_date) DO NOTHING;
END $$;

-- ============================================
-- Sample Tournament Standings (after each round)
-- ============================================

DO $$
DECLARE
    v_tournament_id INT;
    v_player1_id INT;
    v_player2_id INT;
    v_player3_id INT;
    v_player4_id INT;
    v_player5_id INT;
BEGIN
    SELECT id INTO v_tournament_id FROM tournaments WHERE name = 'Тестовый турнир по шахматам 2026';
    SELECT id INTO v_player1_id FROM players WHERE rus_id = 1001;
    SELECT id INTO v_player2_id FROM players WHERE rus_id = 1002;
    SELECT id INTO v_player3_id FROM players WHERE rus_id = 1003;
    SELECT id INTO v_player4_id FROM players WHERE rus_id = 1004;
    SELECT id INTO v_player5_id FROM players WHERE rus_id = 1005;
    
    -- After Round 1
    INSERT INTO tournament_standings (tournament_id, player_id, round_number, points, position) VALUES
    (v_tournament_id, v_player1_id, 1, 1.0, 1),
    (v_tournament_id, v_player2_id, 1, 0.0, 5),
    (v_tournament_id, v_player3_id, 1, 0.5, 3),
    (v_tournament_id, v_player4_id, 1, 0.5, 3),
    (v_tournament_id, v_player5_id, 1, 0.0, 5)
    ON CONFLICT (tournament_id, player_id, round_number) DO NOTHING;
    
    -- After Round 2
    INSERT INTO tournament_standings (tournament_id, player_id, round_number, points, position) VALUES
    (v_tournament_id, v_player1_id, 2, 2.0, 1),
    (v_tournament_id, v_player2_id, 2, 1.0, 3),
    (v_tournament_id, v_player3_id, 2, 1.0, 3),
    (v_tournament_id, v_player4_id, 2, 1.0, 3),
    (v_tournament_id, v_player5_id, 2, 0.5, 5)
    ON CONFLICT (tournament_id, player_id, round_number) DO NOTHING;
    
    -- After Round 3
    INSERT INTO tournament_standings (tournament_id, player_id, round_number, points, position) VALUES
    (v_tournament_id, v_player1_id, 3, 2.5, 1),
    (v_tournament_id, v_player2_id, 3, 1.5, 2),
    (v_tournament_id, v_player3_id, 3, 2.0, 2),
    (v_tournament_id, v_player4_id, 3, 1.5, 2),
    (v_tournament_id, v_player5_id, 3, 0.5, 5)
    ON CONFLICT (tournament_id, player_id, round_number) DO NOTHING;
END $$;

-- ============================================
-- Verification Queries
-- ============================================

-- Run these to verify the sample data was inserted:

-- Check players count
-- SELECT COUNT(*) as player_count FROM players;

-- Check tournament
-- SELECT * FROM tournaments;

-- Check games count
-- SELECT COUNT(*) as game_count FROM games;

-- Check standings
-- SELECT * FROM tournament_standings ORDER BY round_number, position;

-- Check active tournament table view
-- SELECT * FROM v_active_tournament_table;

-- Check player profile view
-- SELECT * FROM v_player_profile;