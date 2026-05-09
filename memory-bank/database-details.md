# Database Details

## Database Schema (MVP)

### Core Tables

#### players
Player information with rating history tracking.

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Primary key |
| rus_id | INTEGER | Russian Federation ID |
| name | VARCHAR(255) | Player's full name |
| gender | CHAR(1) | 'M' or 'F' |
| birth_year | SMALLINT | Year of birth |
| city | VARCHAR(255) | City of residence |

#### tournaments
Tournament metadata.

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(255) | Tournament name |
| location | VARCHAR(255) | Tournament location |
| start_date | DATE | Tournament start date |
| end_date | DATE | Tournament end date |

#### tournament_players
Player participation in tournaments with rating at tournament time.

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Primary key |
| tournament_id | INTEGER | Foreign key to tournaments |
| player_id | INTEGER | Foreign key to players |
| rating_at_tournament | SMALLINT | Player's rating at tournament start |
| games_played | SMALLINT | Number of games played |

#### games
Game results (single score field for white's points).

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Primary key |
| tournament_id | INTEGER | Foreign key to tournaments |
| round | SMALLINT | Round number |
| white_id | INTEGER | Foreign key to players (white) |
| black_id | INTEGER | Foreign key to players (black) |
| score | DECIMAL(3,1) | White's score (1=win, 0.5=draw, 0=loss) |

#### player_ratings
Rating history with dates.

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Primary key |
| player_id | INTEGER | Foreign key to players |
| rating | SMALLINT | Rating value |
| rating_date | DATE | Date of rating |
| source_tournament_id | INTEGER | Foreign key to tournaments (optional) |

#### tournament_standings
Standings snapshots after each round.

| Field | Type | Description |
|-------|------|-------------|
| id | SERIAL | Primary key |
| tournament_id | INTEGER | Foreign key to tournaments |
| player_id | INTEGER | Foreign key to players |
| round | SMALLINT | Round number |
| points | DECIMAL(3,1) | Total points |
| place | SMALLINT | Position in tournament |

### Views

#### v_active_tournament_table
Current standings for active tournaments.

#### v_player_profile
Player profile with statistics.

#### v_player_rating_history
Player's rating history over time.

### Indexes
1. idx_tournaments_dates - for active tournament lookup
2. idx_games_tournament_round - for round results
3. idx_games_white_black - for player game history
4. idx_player_ratings_player_date - for rating history
5. idx_tournament_standings_tournament_round - for standings lookup
6. idx_tournament_players_tournament - for tournament participants
7. idx_tournament_players_player - for player tournaments
8. idx_games_white - for white player games
9. idx_games_black - for black player games
10. idx_player_ratings_player - for player rating history
11. idx_tournament_standings_player - for player standings history

### Triggers

#### game_result_notify
Triggers pg_notify when game results change.

## Database Configuration

### Docker Setup
- PostgreSQL 15
- Database name: `chessfan`
- Username: `chessfan`
- Password: `chessfan123`
- Port: `5432`
- Data volume: `postgres_data`

### Connection String
```
PGPASSWORD=chessfan123 psql -h localhost -p 5432 -U chessfan -d chessfan
```

### Automated Deployment
- Script: `deploy.sh`
- Starts PostgreSQL container via Docker Compose
- Waits for database readiness using pg_isready
- Creates database structure from SQL script
- Verifies all tables, views, and triggers exist

## Data Ingestion

### Byes
When a player gets a point without playing (bye), do NOT create a game record.

### Rating Updates
Ratings are updated only after tournament completion, not in real-time.

### Standings Snapshots
Tournament standings should be snapshotted after each round for historical tracking.