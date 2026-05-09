# Deployment Details

## Automated Deployment Script

### deploy.sh

The deployment script performs the following steps:

1. **Prerequisites Check**
   - Verifies docker, docker-compose, and psql are installed
   - Checks for required configuration files

2. **Container Management**
   - Starts PostgreSQL container via docker-compose
   - Handles existing containers gracefully

3. **PostgreSQL Readiness**
   - Polls database using pg_isready
   - Configurable timeout (30 attempts, 2 second intervals)

4. **Database Structure Creation**
   - Runs SQL initialization script
   - Creates all tables, views, and triggers

5. **Verification**
   - Checks all 6 tables exist
   - Checks all 3 views exist
   - Verifies trigger and function exist
   - Tests database connection

### Usage
```bash
chmod +x deploy.sh
./deploy.sh
```

## Docker Compose Configuration

### docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:15
    container_name: chessfan-postgres
    environment:
      POSTGRES_DB: chessfan
      POSTGRES_USER: chessfan
      POSTGRES_PASSWORD: chessfan123
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docs/db/sql/create.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Quick Start
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

## Database Verification

### Verification Guide
See `docs/deployment/verify.md` for comprehensive verification procedures.

### Quick Verification
```bash
# Check container status
docker ps | grep chessfan-postgres

# Check database readiness
docker exec chessfan-postgres pg_isready -U chessfan

# Verify tables
PGPASSWORD=chessfan123 psql -h localhost -p 5432 -U chessfan -d chessfan -c "\dt"
```

## Environment Variables

### .env.example
```
POSTGRES_DB=chessfan
POSTGRES_USER=chessfan
POSTGRES_PASSWORD=chessfan123
POSTGRES_PORT=5432
```

## Local Deployment

### Prerequisites
- PostgreSQL 13+
- psql client

### Steps
1. Create PostgreSQL database: `createdb chessfan`
2. Run SQL migration scripts: `psql -f docs/db/sql/create.sql`
3. Configure connection string
4. Set up notification listeners

### Connection String
```
PGPASSWORD=chessfan123 psql -h localhost -p 5432 -U chessfan -d chessfan
```

## Monitoring

### Database Monitoring
- Query performance
- Connection pool status
- Replication lag (if applicable)

### Application Monitoring
- API response times
- Error rates
- Data ingestion success/failure

### Logging
- Structured JSON logs
- Error tracking (Sentry or similar)
- Database query logging