# Docker Deployment: Chessfan

## Overview

This guide explains how to deploy the Chessfan application using Docker Compose with PostgreSQL.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)

## Quick Start

### 1. Clone the repository

```bash
git clone git@github.com:ivan-dodik/chessfan.git
cd chessfan
```

### 2. Configure environment (optional)

Copy the example environment file and customize if needed:

```bash
cp .env.example .env
```

### 3. Start PostgreSQL

```bash
docker-compose up -d
```

This command will:
- Pull the PostgreSQL 15 Docker image
- Create a container named `chessfan-postgres`
- Initialize the database with the schema from `docs/db/sql/create.sql`
- Start the database server on port 5432

### 4. Verify the database

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f postgres

# Connect to database
docker-compose exec postgres psql -U chessfan -d chessfan -c "\dt"
```

You should see the following tables:
- players
- tournaments
- tournament_players
- games
- player_ratings
- tournament_standings

## Database Connection

### From host machine

```bash
psql -h localhost -U chessfan -d chessfan -p 5432
```

### From other containers

```bash
# Use the service name as hostname
psql -h postgres -U chessfan -d chessfan -p 5432
```

## Common Commands

### Start database

```bash
docker-compose up -d
```

### Stop database

```bash
docker-compose down
```

### Stop and remove volumes (data loss!)

```bash
docker-compose down -v
```

### View logs

```bash
docker-compose logs -f postgres
```

### Execute SQL commands

```bash
docker-compose exec postgres psql -U chessfan -d chessfan -c "SELECT * FROM players;"
```

### Open psql shell

```bash
docker-compose exec postgres psql -U chessfan -d chessfan
```

## Data Persistence

Database data is stored in a Docker volume named `postgres_data`. This ensures data persists across container restarts.

To backup the database:

```bash
docker-compose exec postgres pg_dump -U chessfan chessfan > backup.sql
```

To restore from backup:

```bash
docker-compose exec -i postgres psql -U chessfan -d chessfan < backup.sql
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| POSTGRES_DB | chessfan | Database name |
| POSTGRES_USER | chessfan | Database user |
| POSTGRES_PASSWORD | chessfan123 | Database password |
| POSTGRES_PORT | 5432 | Database port |

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs postgres

# Common issue: port already in use
# Change POSTGRES_PORT in .env or stop other PostgreSQL instance
```

### Database initialization failed

```bash
# Remove container and volume, then restart
docker-compose down -v
docker-compose up -d
```

### Connection refused

```bash
# Ensure container is running
docker-compose ps

# Check if port is listening
netstat -tlnp | grep 5432
```

## Production Deployment

For production use, consider:

1. **Use stronger passwords** - Change default credentials
2. **Use named volumes** - For better backup management
3. **Enable SSL** - Configure PostgreSQL SSL connections
4. **Use secrets** - Store passwords via Docker secrets
5. **Backup strategy** - Implement regular backups
6. **Resource limits** - Set CPU/memory limits

Example production `docker-compose.yml` modifications:

```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # From .env or secrets
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./certs:/etc/ssl/certs:ro
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Next Steps

After PostgreSQL is running:

1. [Database documentation](../db/README.md)
2. [Data ingestion setup](../../ingestion/README.md)
3. [API server setup](../../api/README.md)
4. [Frontend setup](../../frontend/README.md)