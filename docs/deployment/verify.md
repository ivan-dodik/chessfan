# Database Verification Guide

## Overview

This guide explains how to verify that the Chessfan database has been successfully deployed and is ready to accept data.

## Quick Verification

### Using the Deployment Script

Run the deployment script with the `--verify` flag (if available) or simply run it - verification is built-in:

```bash
./deploy.sh
```

The script automatically verifies all database structures after creation.

### Manual Verification

#### 1. Check Container Status

```bash
docker compose ps
```

Expected output should show `chessfan-postgres` as `Up`:

```
NAME                STATUS              PORTS
chessfan-postgres   Up (healthy)        0.0.0.0:5432->5432/tcp
```

#### 2. Check Database Connection

```bash
docker compose exec postgres pg_isready -U chessfan -d chessfan
```

Expected output:
```
Host:     localhost
Port:     5432
Database: chessfan
User:     chessfan
pg_isready: connection accepted
```

#### 3. List All Tables

```bash
docker compose exec postgres psql -U chessfan -d chessfan -c "\dt"
```

Expected tables:
```
List of relations
Schema |       Name        | Type  | Owner
-------+-------------------+-------+--------
public | games             | table | chessfan
public | player_ratings    | table | chessfan
public | players           | table | chessfan
public | tournaments       | table | chessfan
public | tournament_players| table | chessfan
public | tournament_standings | table | chessfan
(6 rows)
```

#### 4. List All Views

```bash
docker compose exec postgres psql -U chessfan -d chessfan -c "\dv"
```

Expected views:
```
List of relations
Schema |         Name          | Type | Owner
-------+-----------------------+------+--------
public | v_active_tournament_table | view | chessfan
public | v_player_profile      | view | chessfan
public | v_player_rating_history | view | chessfan
(3 rows)
```

#### 5. Check Trigger

```bash
docker compose exec postgres psql -U chessfan -d chessfan -c "\d games"
```

Look for the trigger in the output:
```
Triggers:
    trg_notify_game_result_change AFTER INSERT OR UPDATE OR DELETE ON games FOR EACH ROW EXECUTE FUNCTION notify_game_result_change()
```

#### 6. Test pg_notify Function

```bash
docker compose exec postgres psql -U chessfan -d chessfan -c "SELECT proname FROM pg_proc WHERE proname = 'notify_game_result_change';"
```

Expected output:
```
proname
-------------------------
notify_game_result_change
(1 row)
```

## Detailed Verification

### Verify Table Structure

#### Players Table

```bash
docker compose exec postgres psql -U chessfan -d chessfan -c "\d players"
```

Should show:
- id (SERIAL PRIMARY KEY)
- rus_id (INTEGER UNIQUE)
- name (VARCHAR(200) NOT NULL)
- gender (CHAR(1) NOT NULL)
- birth_year (SMALLINT)
- city (VARCHAR(100))
- created_at (TIMESTAMPTZ DEFAULT NOW())

#### Tournaments Table

```bash
docker compose exec postgres psql -U chessfan -d chessfan -c "\d tournaments"
```

Should show:
- id (SERIAL PRIMARY KEY)
- name (VARCHAR(300) NOT NULL)
- location (VARCHAR(200))
- start_date (DATE NOT NULL)
- end_date (DATE NOT NULL)
- created_at (TIMESTAMPTZ DEFAULT NOW())

#### Games Table

```bash
docker compose exec postgres psql -U chessfan -d chessfan -c "\d games"
```

Should show:
- id (SERIAL PRIMARY KEY)
- tournament_id (INTEGER NOT NULL FK)
- round (SMALLINT NOT NULL)
- white_player_id (INTEGER NOT NULL FK)
- black_player_id (INTEGER NOT NULL FK)
- score (DECIMAL(3,1) NOT NULL)
- created_at (TIMESTAMPTZ DEFAULT NOW())

### Verify Indexes

```bash
docker compose exec postgres psql -U chessfan -d chessfan -c "\di"
```

Should show 11 indexes for the tables.

### Verify Foreign Key Constraints

```bash
docker compose exec postgres psql -U chessfan -d chessfan -c "SELECT tc.table_name, tc.constraint_name, ccu.column_name, ccu.table_name AS foreign_table_name FROM information_schema.table_constraints tc JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name WHERE tc.constraint_type = 'FOREIGN KEY';"
```

Should show foreign key relationships for:
- tournament_players.tournament_id → tournaments.id
- tournament_players.player_id → players.id
- games.tournament_id → tournaments.id
- games.white_player_id → players.id
- games.black_player_id → players.id
- player_ratings.player_id → players.id
- tournament_standings.tournament_id → tournaments.id
- tournament_standings.player_id → players.id

## Common Issues

### Container Not Starting

```bash
# Check logs
docker compose logs postgres

# Common issue: port already in use
# Stop other PostgreSQL instance or change port in docker-compose.yml
```

### Database Not Accepting Connections

```bash
# Wait a bit and try again
sleep 10
docker compose exec postgres pg_isready

# Check if PostgreSQL is fully initialized
docker compose logs postgres | grep "database system is ready"
```

### SQL Script Failed

```bash
# Check if SQL file exists
ls -la docs/db/sql/create.sql

# Manually run the script
docker compose exec -T postgres psql -U chessfan -d chessfan -f /docker-entrypoint-initdb.d/init.sql
```

### Missing Tables/Views

```bash
# Check if schema was created
docker compose exec postgres psql -U chessfan -d chessfan -c "\dt public.*"

# Check schema version
docker compose exec postgres psql -U chessfan -d chessfan -c "SELECT * FROM information_schema.schemata WHERE schema_name = 'public';"
```

## Verification Checklist

- [ ] Container is running (`docker compose ps`)
- [ ] PostgreSQL is ready (`pg_isready` returns success)
- [ ] All 6 tables exist
- [ ] All 3 views exist
- [ ] Trigger `trg_notify_game_result_change` exists
- [ ] Function `notify_game_result_change` exists
- [ ] All 11 indexes exist
- [ ] Foreign key constraints are in place
- [ ] Can connect to database with credentials
- [ ] Can query tables (e.g., `SELECT COUNT(*) FROM players`)

## Next Steps

After successful verification:

1. [Load sample data](../../ingestion/README.md)
2. [Set up data ingestion](../../ingestion/README.md)
3. [Start API server](../../api/README.md)
4. [Start frontend](../../frontend/README.md)