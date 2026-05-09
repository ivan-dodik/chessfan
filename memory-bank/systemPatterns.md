# System Patterns: Chessfan

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Chessfan Application                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐ │
│  │   Data Ingestion│────▶│   API Layer     │────▶│   Frontend      │ │
│  │   (External     │     │   (REST/GraphQL│     │   (Next.js)     │ │
│  │    Programs)    │     │    Layer)       │     │                 │ │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘ │
│              │                   │                                   │
│              ▼                   ▼                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL Database                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐  │   │
│  │  │   Players   │  │ Tournaments │  │   Rating History     │  │   │
│  │  │   Table     │  │   Table     │  │   (Snapshots)        │  │   │
│  │  └─────────────┘  └─────────────┘  └──────────────────────┘  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐  │   │
│  │  │   Games     │  │ Standings   │  │   Tournament Stats   │  │   │
│  │  │   Table     │  │   Table     │  │   (Views)            │  │   │
│  │  └─────────────┘  └─────────────┘  └──────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Notification Service                      │   │
│  │                    (pg_notify)                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Technical Decisions

### Database Design Principles
1. **Historical Data**: Store snapshots of ratings and standings after each tournament/round
2. **External Ingestion**: Data written by external programs, not real-time
3. **Minimal Fields**: No created_at/updated_at in most tables (except debugging)
4. **No PGN**: PGN notation excluded from MVP
5. **No Exact Times**: Only tournament dates, not game start/end times
6. **Single Score Field**: Games table uses single `score` field (white's points)
7. **rus_id**: Russian Federation ID instead of FIDE ID

### Table Structure Principles
1. **Separate Tournament Participation**: One player can participate in multiple tournaments with different ratings
2. **Rating History**: Store rating changes over time for trend analysis
3. **Standings Snapshots**: Capture tournament position after each round
4. **Bye Handling**: Special handling for players who get points without playing (no game record)

## Component Relationships

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Flow Diagram                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. External Scraper (Python)                                       │
│     ├─ Fetch from chess-results.com                                 │
│     ├─ Parse tournament data                                        │
│     ├─ Extract player information                                   │
│     └─ Process game results                                         │
│                                                                       │
│  2. Data Validation Layer                                           │
│     ├─ Validate player IDs                                          │
│     ├─ Check tournament dates                                       │
│     └─ Handle missing data                                          │
│                                                                       │
│  3. Database Ingestion                                              │
│     ├─ UPSERT players                                               │
│     ├─ UPSERT tournaments                                           │
│     ├─ Insert game results                                          │
│     ├─ Update standings snapshots                                   │
│     └─ Update rating history                                        │
│                                                                       │
│  4. Notification Trigger                                            │
│     ├─ Detect game result changes                                   │
│     ├─ Send pg_notify events                                        │
│     └─ Update real-time feeds                                       │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Critical Implementation Paths

### Path 1: Tournament Data Ingestion
1. Scraper fetches tournament page from chess-results.com
2. Parse player list, rounds, and game results
3. Validate and upsert player records
4. Create tournament record if new
5. Insert game results with proper pairing logic
6. Update tournament standings snapshot

### Path 2: Rating History Tracking
1. After tournament completion, fetch updated ratings
2. Create rating snapshot for each player
3. Store historical rating with tournament reference
4. Update current rating in player record

### Path 3: Live Standings Calculation
1. Query games for active tournament
2. Calculate points for each player
3. Generate standings snapshot
4. Store with round reference
5. Trigger notification for significant changes

## API Design Patterns

### Player Endpoints
- `GET /players/{id}` - Player profile with rating history
- `GET /players/{id}/tournaments` - Tournament participation
- `GET /players/{id}/games` - Game history
- `GET /players/{id}/ratings` - Rating history

### Tournament Endpoints
- `GET /tournaments` - List tournaments
- `GET /tournaments/{id}` - Tournament details
- `GET /tournaments/{id}/standings` - Current standings
- `GET /tournaments/{id}/rounds` - Round results

### Statistics Endpoints
- `GET /stats/player-vs-player` - Head-to-head statistics
- `GET /stats/player-performance` - Performance metrics
- `GET /stats/tournament-summary` - Tournament statistics

## Database Schema (MVP)

### Core Tables
| Table | Description |
|-------|-------------|
| `players` | Player information (id, rus_id, name, gender, birth_year, city) |
| `tournaments` | Tournament metadata (name, location, dates) |
| `tournament_players` | Player participation with rating_at_tournament |
| `games` | Game results (single score field for white's points) |
| `player_ratings` | Rating history with dates |
| `tournament_standings` | Standings snapshots after each round |

### Views
| View | Description |
|------|-------------|
| `v_active_tournament_table` | Current standings for active tournaments |
| `v_player_profile` | Player profile with statistics |
| `v_player_rating_history` | Player's rating history over time |

### Indexes
- Tournament and player lookups
- Game lookups by tournament, round, and player
- Rating history lookups by player and date
- Standings lookups by tournament and round

## Configuration

### Database Setup (Docker)
- PostgreSQL 15 (via Docker Compose)
- Database name: `chessfan`
- Username: `chessfan`
- Password: `chessfan123`
- Port: `5432`
- Data volume: `postgres_data`
- Auto-initialization: `docs/db/sql/create.sql`

### Automated Deployment
- Script: `deploy.sh` in project root
- Starts PostgreSQL container via Docker Compose
- Waits for database readiness using pg_isready
- Creates database structure from SQL script
- Verifies all tables, views, and triggers exist
- Documentation: `docs/deployment/verify.md`

### Current Database Status
- PostgreSQL running in Docker container (chessfan-postgres)
- Sample data loaded: 5 players, 1 tournament, 10 games, 10 ratings, 15 standings
- pg_notify functionality verified
- Connection: `PGPASSWORD=chessfan123 psql -h localhost -p 5432 -U chessfan -d chessfan`

### Database Setup (Local)
- PostgreSQL 13+
- Database name: `chessfan`
- User: postgres (or custom user)

### Docker Quick Start
```bash
# Start PostgreSQL
docker-compose up -d

# Stop PostgreSQL
docker-compose down

# View logs
docker-compose logs -f postgres

# Connect to database
docker-compose exec postgres psql -U chessfan -d chessfan
```

### Notification Setup
- Channel: `game_result_changes`
- Payload format: JSON
- Events: game_created, game_updated, game_deleted