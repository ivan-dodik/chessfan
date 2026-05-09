# Chessfan MVP - Database Documentation

## Overview

This directory contains the database schema and documentation for the Chessfan MVP - a chess tournament monitoring service.

## Directory Structure

```
docs/db/
├── README.md          # This file
├── schema.md          # Database schema description
├── sql/
│   └── create.sql     # SQL script to create the database
├── views.md           # Database views documentation
└── triggers.md        # Triggers and notifications documentation

docs/deployment/
├── docker.md          # Docker deployment guide
├── verify.md          # Database verification guide
└── deploy.sh          # Deployment script (in project root)
```

## Quick Start

### Option 1: Automated Deployment (Recommended)

Use the deployment script for automated setup:

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
1. Start PostgreSQL container
2. Wait for database to be ready
3. Create database structure
4. Verify all tables, views, and triggers

See [Deployment Verification](../deployment/verify.md) for verification details.

### Option 2: Using Docker Compose (Manual)

1. Ensure Docker and Docker Compose are installed

2. Start PostgreSQL with:
```bash
docker-compose up -d
```

3. Verify the database:
```bash
docker-compose exec postgres psql -U chessfan -d chessfan -c "\dt"
```

See [Docker Deployment Guide](../deployment/docker.md) for more details.

### Option 3: Local PostgreSQL Installation

1. Prerequisites:
   - PostgreSQL 13+
   - psql client

2. Create a new database:
```bash
createdb chessfan
```

3. Run the SQL script:
```bash
psql -h localhost -U postgres -d chessfan -f docs/db/sql/create.sql
```

4. Verify installation:
```bash
psql -h localhost -U postgres -d chessfan -c "\dt"
```

You should see:
- players
- tournaments
- tournament_players
- games
- player_ratings
- tournament_standings

## Data Loading Order

Load data in this order to respect foreign key constraints:

1. **players** - Player information
2. **tournaments** - Tournament metadata
3. **tournament_players** - Player participation in tournaments
4. **games** - Game results
5. **player_ratings** - Rating history (after tournament completion)
6. **tournament_standings** - Standings snapshots (after each round)

## Handling "Bye" Situations

When a player receives a "bye" (gets a point without playing):

- **Do NOT create a game record** in the `games` table
- Add 1 point directly when generating `tournament_standings` snapshots

## Live Notifications

The database sends notifications when game results change:

```sql
-- Subscribe to notifications
LISTEN game_result_changes;

-- When a game is inserted/updated/deleted, you'll receive:
-- channel: "game_result_changes"
-- payload: JSON with game details
```

## Available Views

- `v_active_tournament_table` - Current standings for each active tournament
- `v_player_profile` - Player profile with statistics
- `v_player_rating_history` - Player's rating history

See `views.md` for more details.

## Troubleshooting

### Error: "permission denied for schema public"

```bash
GRANT ALL ON SCHEMA public TO your_user;
```

### Error: "relation does not exist"

Make sure you ran the SQL script in the correct order and database.

### Notifications not working?

Check PostgreSQL configuration:
```sql
SHOW listen_addresses;
SHOW port;
```

Ensure `pg_notify` is enabled (it is by default).