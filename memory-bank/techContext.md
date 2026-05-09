# Tech Context: Chessfan

## Technology Stack

### Database
- **PostgreSQL 13+** - Primary database
  - JSON support for flexible data storage
  - pg_notify for real-time notifications
  - Window functions for standings calculations
  - Views for simplified queries

### Backend
- **Python** - Data ingestion and scraping
  - BeautifulSoup - HTML parsing
  - Playwright - Dynamic content loading
  - psycopg2 / asyncpg - PostgreSQL connection
- **FastAPI / NestJS** - API layer (choice pending)
  - REST API for data access
  - WebSockets for real-time updates

### Frontend
- **Next.js 16+** - Web application framework
  - App Router for routing
  - Server Components for performance
  - Client Components for interactivity
  - Cache Components mode for caching

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration (PostgreSQL)
- **Git** - Version control (GitHub)
- **Bash** - Deployment scripts

## Development Setup

### Prerequisites
- Node.js 18+ (for Next.js)
- Python 3.10+ (for data ingestion)
- PostgreSQL 13+ (local or remote)
- npm/pnpm/yarn/bun (package manager)

### Project Structure
```
chessfan/
├── deploy.sh            # Automated deployment script
├── docker-compose.yml   # PostgreSQL configuration
├── .env.example         # Environment variables template
├── memory-bank/         # Project documentation
├── planning/            # Planning documents (locked)
├── docs/                # Documentation
│   ├── db/              # Database documentation
│   └── deployment/      # Deployment documentation
├── scraper/             # Data scraping and ingestion
│   └── src/
├── api/                 # API server (future)
│   └── src/
└── frontend/            # Next.js application (future)
    ├── app/
    └── components/
```

### Database Setup (Automated)
1. Run `./deploy.sh` to start PostgreSQL and create database structure
2. Script automatically waits for readiness and verifies all components
3. Connect via `PGPASSWORD=chessfan123 psql -h localhost -p 5432 -U chessfan -d chessfan`

### Current Database Status
- PostgreSQL running in Docker container (chessfan-postgres)
- Sample data loaded: 5 players, 1 tournament, 10 games, 10 ratings, 15 standings
- pg_notify functionality verified
- Connection: `PGPASSWORD=chessfan123 psql -h localhost -p 5432 -U chessfan -d chessfan`

### Database Setup (Docker Compose - Manual)
1. Copy `.env.example` to `.env` and customize if needed
2. Run `docker-compose up -d` to start PostgreSQL
3. Database auto-initializes with `docs/db/sql/create.sql`
4. Connect via `psql -h localhost -U chessfan -d chessfan`

### Database Setup (Local)
1. Create PostgreSQL database: `createdb chessfan`
2. Run SQL migration scripts: `psql -f docs/db/sql/create.sql`
3. Configure connection string
4. Set up notification listeners

### Data Ingestion Pipeline
1. Configure scraper targets (chess-results.com URLs)
2. Run ingestion scripts periodically
3. Validate and transform data
4. Insert into database
5. Trigger notifications

## Technical Constraints

### Database Constraints
- No created_at/updated_at in most tables (except debugging)
- No PGN notation in MVP
- No exact game start/end times
- Ratings updated only after tournament completion
- Single score field in games table (white's points only)
- rus_id instead of fide_id for Russian Federation ID

### Data Source Constraints
- chess-results.com is the primary data source
- Russian Chess Federation website for ratings
- No official API - requires web scraping
- Data availability varies by tournament

### Performance Considerations
- Standings calculated from game results (not pre-computed)
- Rating history stored for trend analysis
- Snapshots created after each round for historical standings
- pg_notify for real-time updates to connected clients
- Indexes on foreign keys and common query patterns

## Dependencies

### Python Dependencies (Ingestion)
- requests - HTTP requests
- beautifulsoup4 - HTML parsing
- playwright - Dynamic content loading
- psycopg2 or asyncpg - PostgreSQL connection
- python-dotenv - Environment configuration

### JavaScript Dependencies (Frontend)
- next - Next.js framework
- react - UI library
- react-dom - React DOM renderer
- pg - PostgreSQL client
- zod - Schema validation

## Build and Deployment

### Development
```bash
# Start database (Docker)
docker-compose up -d

# Run ingestion
cd scraper && python -m src.chess_results_parser

# Start API
cd api && npm run dev

# Start frontend
cd frontend && npm run dev
```

### Production
- Database: PostgreSQL on cloud provider or dedicated server
- API: Node.js server with PM2 or similar
- Frontend: Next.js with static export or server deployment
- Ingestion: Scheduled cron jobs or CI/CD pipeline

## Testing Strategy

### Unit Tests
- Data parsing logic
- Validation rules
- API endpoint handlers

### Integration Tests
- Database operations
- Data ingestion pipeline
- API integration

### E2E Tests
- Frontend user flows
- Data display accuracy
- Real-time updates

## Monitoring and Logging

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