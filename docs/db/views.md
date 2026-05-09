# Database Views

## Overview

This document describes the database views available in Chessfan MVP.

## Available Views

### v_active_tournament_table

Current standings for each active tournament.

**Purpose:** Display the live tournament table showing player positions, points, and round information.

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| tournament_id | INTEGER | Tournament ID |
| tournament_name | VARCHAR(300) | Tournament name |
| start_date | DATE | Tournament start date |
| end_date | DATE | Tournament end date |
| player_id | INTEGER | Player ID |
| player_name | VARCHAR(200) | Player name |
| points | DECIMAL(4,1) | Accumulated points |
| position | SMALLINT | Position in standings |
| round_number | SMALLINT | Round number for this snapshot |

**Usage:**
```sql
-- Get current standings for all active tournaments
SELECT * FROM v_active_tournament_table ORDER BY tournament_id, position;

-- Get standings for a specific tournament
SELECT * FROM v_active_tournament_table WHERE tournament_id = 1 ORDER BY position;
```

---

### v_player_profile

Player profile with statistics.

**Purpose:** Display a player's basic information, rating, and tournament statistics.

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| player_id | INTEGER | Player ID |
| player_name | VARCHAR(200) | Player name |
| gender | CHAR(1) | Gender (M/F) |
| birth_year | SMALLINT | Birth year |
| city | VARCHAR(100) | City of residence |
| rus_id | INTEGER | Russian Federation ID |
| current_rating | SMALLINT | Latest known rating |
| tournaments_played | INTEGER | Number of tournaments played |
| games_played | INTEGER | Number of games played |
| wins | INTEGER | Number of wins |
| draws | INTEGER | Number of draws |
| losses | INTEGER | Number of losses |

**Usage:**
```sql
-- Get profile for a specific player
SELECT * FROM v_player_profile WHERE player_id = 1;

-- Get all players ordered by rating
SELECT player_name, current_rating, city FROM v_player_profile ORDER BY current_rating DESC;
```

---

### v_player_rating_history

Player's rating history.

**Purpose:** Track how a player's rating has changed over time.

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| player_id | INTEGER | Player ID |
| player_name | VARCHAR(200) | Player name |
| rating | SMALLINT | Rating value |
| rating_date | DATE | Date for which rating is valid |
| tournament_name | VARCHAR(300) | Tournament name (if rating changed after tournament) |

**Usage:**
```sql
-- Get rating history for a specific player
SELECT rating_date, rating, tournament_name 
FROM v_player_rating_history 
WHERE player_id = 1 
ORDER BY rating_date;

-- Get all rating changes for a tournament
SELECT player_name, rating, rating_date 
FROM v_player_rating_history 
WHERE tournament_name = 'Moscow Open 2024' 
ORDER BY rating DESC;
```

---

## Adding New Views

To add a new view, follow this pattern:

```sql
CREATE VIEW v_view_name AS
SELECT ...
FROM ...
WHERE ...
ORDER BY ...;
```

Remember to:
1. Add documentation in this file
2. Update the README.md if the view is important for users