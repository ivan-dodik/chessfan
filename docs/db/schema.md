# Database Schema

## Overview

This document describes the database schema for Chessfan MVP - a chess tournament monitoring service.

## Tables

### players

Player information.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key, auto-increment |
| rus_id | INTEGER | Player ID in Russian Chess Federation (unique) |
| name | VARCHAR(200) | Full player name |
| gender | CHAR(1) | Gender: 'M' or 'F' |
| birth_year | SMALLINT | Birth year (NULL if unknown) |
| city | VARCHAR(100) | City of residence |
| created_at | TIMESTAMPTZ | Creation timestamp |

**Constraints:**
- PRIMARY KEY: `id`
- UNIQUE: `rus_id`
- CHECK: `gender IN ('M', 'F')`

---

### tournaments

Tournament metadata.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(300) | Tournament name |
| location | VARCHAR(200) | City/country location |
| start_date | DATE | Start date |
| end_date | DATE | End date |
| created_at | TIMESTAMPTZ | Creation timestamp |

**Constraints:**
- PRIMARY KEY: `id`

---

### tournament_players

Player participation in tournaments.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| tournament_id | INTEGER | Tournament reference (FK) |
| player_id | INTEGER | Player reference (FK) |
| rating_at_tournament | SMALLINT | Player rating at tournament time |
| title | VARCHAR(20) | Title (IM, FM, CM, NULL) |
| seed | SMALLINT | Seed number (NULL if none) |

**Constraints:**
- PRIMARY KEY: `id`
- FOREIGN KEY: `tournament_id` → `tournaments(id)`
- FOREIGN KEY: `player_id` → `players(id)`
- UNIQUE: `tournament_id`, `player_id`

---

### games

Game results.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| tournament_id | INTEGER | Tournament reference (FK) |
| round | SMALLINT | Round number (1, 2, 3...) |
| white_player_id | INTEGER | White player reference (FK) |
| black_player_id | INTEGER | Black player reference (FK) |
| score | DECIMAL(3,1) | White player's score (1=win, 0.5=draw, 0=loss) |
| created_at | TIMESTAMPTZ | Creation timestamp |

**Constraints:**
- PRIMARY KEY: `id`
- FOREIGN KEY: `tournament_id` → `tournaments(id)`
- FOREIGN KEY: `white_player_id` → `players(id)`
- FOREIGN KEY: `black_player_id` → `players(id)`
- CHECK: `score IN (0, 0.5, 1)`
- CHECK: `white_player_id != black_player_id`

**Note:** Black player's score = `1 - score`.

---

### player_ratings

Player rating history.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| player_id | INTEGER | Player reference (FK) |
| rating | SMALLINT | Rating value |
| rating_date | DATE | Date for which rating is valid |
| source_tournament_id | INTEGER | Tournament reference (FK, NULL) |
| created_at | TIMESTAMPTZ | Creation timestamp |

**Constraints:**
- PRIMARY KEY: `id`
- FOREIGN KEY: `player_id` → `players(id)`
- FOREIGN KEY: `source_tournament_id` → `tournaments(id)`

---

### tournament_standings

Tournament standings snapshots (after each round).

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| tournament_id | INTEGER | Tournament reference (FK) |
| player_id | INTEGER | Player reference (FK) |
| round_number | SMALLINT | Round number |
| points | DECIMAL(4,1) | Accumulated points |
| position | SMALLINT | Position in standings |
| created_at | TIMESTAMPTZ | Creation timestamp |

**Constraints:**
- PRIMARY KEY: `id`
- FOREIGN KEY: `tournament_id` → `tournaments(id)`
- FOREIGN KEY: `player_id` → `players(id)`
- UNIQUE: `tournament_id`, `player_id`, `round_number`

---

## Indexes

| Index Name | Table | Columns |
|------------|-------|---------|
| idx_tournament_players_tournament | tournament_players | tournament_id |
| idx_tournament_players_player | tournament_players | player_id |
| idx_games_tournament | games | tournament_id |
| idx_games_round | games | tournament_id, round |
| idx_games_white | games | white_player_id |
| idx_games_black | games | black_player_id |
| idx_player_ratings_player | player_ratings | player_id |
| idx_player_ratings_date | player_ratings | player_id, rating_date |
| idx_tournament_standings_tournament | tournament_standings | tournament_id |
| idx_tournament_standings_round | tournament_standings | tournament_id, round_number |
| idx_tournaments_dates | tournaments | start_date, end_date |

---

## Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    players      │     │   tournaments   │     │ tournament_players│
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ rus_id (U)      │     │ name            │     │ tournament_id (FK)│
│ name            │     │ location        │     │ player_id (FK)  │
│ gender          │     │ start_date      │     │ rating_at_tournament│
│ birth_year      │     │ end_date        │     │ title           │
│ city            │     │ created_at      │     │ seed            │
│ created_at      │     └─────────────────┘     └─────────────────┘
└─────────────────┘                             │ UNIQUE(t,p)     │
        │                                       └─────────────────┘
        │                                               │     │
        │                                               │     │
        ▼                                               ▼     ▼
┌─────────────────┐                             ┌─────────────────┐
│     games       │                             │ player_ratings  │
├─────────────────┤                             ├─────────────────┤
│ id (PK)         │                             │ id (PK)         │
│ tournament_id (FK)                            │ player_id (FK)  │
│ round           │                             │ rating          │
│ white_player_id (FK)                          │ rating_date     │
│ black_player_id (FK)                          │ source_tournament_id (FK)│
│ score           │                             │ created_at      │
│ created_at      │                             └─────────────────┘
└─────────────────┘                                     │
        │                                               │
        │                                               ▼
        ▼                                       ┌─────────────────┐
┌─────────────────┐                             │tournament_standings│
│player_ratings   │                             ├─────────────────┤
├─────────────────┤                             │ id (PK)         │
│ id (PK)         │                             │ tournament_id (FK)│
│ player_id (FK)  │                             │ player_id (FK)  │
│ rating          │                             │ round_number    │
│ rating_date     │                             │ points          │
│ source_tournament_id (FK)                   │ position        │
│ created_at      │                             │ created_at      │
└─────────────────┘                             │ UNIQUE(t,p,r)   │
                                                └─────────────────┘