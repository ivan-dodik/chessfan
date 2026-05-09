# Changes Log

## 2026-05-10 - Initial Database Schema Implementation

### Summary
Created complete database schema for Chessfan MVP with documentation.

### Files Created

#### Documentation
- `docs/db/README.md` - Main documentation for database setup and usage
- `docs/db/schema.md` - Database schema description with tables and relationships
- `docs/db/views.md` - Database views documentation
- `docs/db/triggers.md` - Triggers and notifications documentation

#### SQL Scripts
- `docs/db/sql/create.sql` - Complete SQL script to create database objects

### Database Objects Created

#### Tables (6)
1. `players` - Player information (id, rus_id, name, gender, birth_year, city, created_at)
2. `tournaments` - Tournament metadata (id, name, location, start_date, end_date, created_at)
3. `tournament_players` - Player participation (id, tournament_id, player_id, rating_at_tournament, title, seed)
4. `games` - Game results (id, tournament_id, round, white_player_id, black_player_id, score, created_at)
5. `player_ratings` - Rating history (id, player_id, rating, rating_date, source_tournament_id, created_at)
6. `tournament_standings` - Standings snapshots (id, tournament_id, player_id, round_number, points, position, created_at)

#### Indexes (11)
- idx_tournament_players_tournament
- idx_tournament_players_player
- idx_games_tournament
- idx_games_round
- idx_games_white
- idx_games_black
- idx_player_ratings_player
- idx_player_ratings_date
- idx_tournament_standings_tournament
- idx_tournament_standings_round
- idx_tournaments_dates

#### Views (3)
- v_active_tournament_table - Current standings for active tournaments
- v_player_profile - Player profile with statistics
- v_player_rating_history - Player rating history

#### Triggers and Functions (1)
- notify_game_result_change() - Function for pg_notify
- trg_notify_game_result_change - Trigger on games table

### Key Design Decisions

1. **rus_id instead of fide_id** - Russian Federation ID as primary external identifier
2. **City field** - Added to players table for player location tracking
3. **Single score field** - Replaced white_score/black_score with single score field (white's points)
4. **No federation column** - Removed as per requirements
5. **No tiebreak columns** - Removed tiebreak1/tiebreak2 from standings table
6. **created_at only for debugging** - Minimal timestamp fields as specified

### Schema Modifications

- Removed `federation` column from `tournament_players`
- Removed `tiebreak1`, `tiebreak2` columns from `tournament_standings`
- Changed `fide_id` to `rus_id` in `players`
- Added `city` column to `players`
- Replaced `white_score` and `black_score` with `score` in `games`

### Next Steps

1. Deploy database to PostgreSQL server
2. Load sample data
3. Test notifications with pg_notify
4. Build data ingestion pipeline
5. Implement API endpoints