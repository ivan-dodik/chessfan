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
│  │  │   Table     │  │   Table     │  │   (Views/Materialized│  │   │
│  │  └─────────────┘  └─────────────┘  └──────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Notification Service                      │   │
│  │                    (pg_notify / Kafka)                       │   │
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

### Table Structure Principles
1. **Separate Tournament Participation**: One player can participate in multiple tournaments with different ratings
2. **Rating History**: Store rating changes over time for trend analysis
3. **Standings Snapshots**: Capture tournament position after each round
4. **Bye Handling**: Special handling for players who get points without playing

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
│     └─ Update standings snapshots                                   │
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

## Data Models (MVP)

### Core Tables
- `players` - Player information
- `tournaments` - Tournament metadata
- `tournament_players` - Player participation records
- `games` - Game results
- `player_ratings` - Rating history
- `tournament_standings` - Standings snapshots

### Views
- `v_player_profile` - Combined player information
- `v_active_tournament_table` - Current standings
- `v_player_tournament_stats` - Tournament statistics per player