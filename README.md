# Chessfan

Chess tournaments and player stats monitoring service.

## Overview

Chessfan helps chess fans track their favorite players' games on offline tournaments, monitor rating changes, and receive notifications about results.

## Quick Start

### Prerequisites

- Docker (version 20.10+) with compose plugin
- PostgreSQL client (psql)

### Deployment

Run the automated deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

This will:
1. Start PostgreSQL container
2. Create database structure (tables, views, triggers)
3. Verify everything is ready

See [Database Documentation](docs/db/README.md) for more details.

## Project Structure

```
chessfan/
├── deploy.sh              # Automated deployment script
├── docker-compose.yml     # PostgreSQL configuration
├── .env.example           # Environment variables template
├── memory-bank/           # Project documentation
│   ├── projectbrief.md    # Project overview and requirements
│   ├── productContext.md  # Product goals and user experience
│   ├── activeContext.md   # Current work status
│   ├── systemPatterns.md  # Architecture and patterns
│   ├── techContext.md     # Technology stack
│   └── progress.md        # Project progress
│   ├── database-details.md    # Detailed database schema
│   ├── scraper-details.md     # Scraper architecture and parsers
│   ├── deployment-details.md  # Deployment procedures
│   └── changelog.md           # Project changelog
├── docs/
│   ├── db/                # Database documentation
│   │   ├── README.md      # Database setup guide
│   │   ├── schema.md      # Database schema
│   │   └── sql/           # SQL scripts
│   └── deployment/        # Deployment guides
│       ├── docker.md      # Docker deployment
│       └── verify.md      # Verification guide
├── planning/              # Planning documents (locked)
└── scraper/               # Data scraping and ingestion
```

## Documentation

| Topic | Documentation |
|-------|---------------|
| Database Setup | [docs/db/README.md](docs/db/README.md) |
| Docker Deployment | [docs/deployment/docker.md](docs/deployment/docker.md) |
| Database Verification | [docs/deployment/verify.md](docs/deployment/verify.md) |
| Database Schema | [docs/db/schema.md](docs/db/schema.md) |
| Views & Triggers | [docs/db/views.md](docs/db/views.md), [docs/db/triggers.md](docs/db/triggers.md) |

## Memory Bank

The project uses a Memory Bank system to maintain project documentation across sessions:

### Core Files (Required)
- **[projectbrief.md](memory-bank/projectbrief.md)** - Project overview and requirements
- **[productContext.md](memory-bank/productContext.md)** - Product goals and user experience
- **[activeContext.md](memory-bank/activeContext.md)** - Current work status and next steps
- **[systemPatterns.md](memory-bank/systemPatterns.md)** - Architecture and design patterns
- **[techContext.md](memory-bank/techContext.md)** - Technology stack and setup
- **[progress.md](memory-bank/progress.md)** - Project progress and milestones

### Additional Context
- **[database-details.md](memory-bank/database-details.md)** - Detailed database schema
- **[scraper-details.md](memory-bank/scraper-details.md)** - Scraper architecture and parsers
- **[deployment-details.md](memory-bank/deployment-details.md)** - Deployment procedures
- **[changelog.md](memory-bank/changelog.md)** - Project changelog

See the [Memory Bank documentation](https://docs.cline.bot/memory-bank) for more information.

## Database Schema

The database includes:
- **6 Tables**: players, tournaments, tournament_players, games, player_ratings, tournament_standings
- **11 Indexes**: For query optimization
- **3 Views**: v_active_tournament_table, v_player_profile, v_player_rating_history
- **1 Trigger**: pg_notify for live game result notifications

## Next Steps

1. [Database Documentation](docs/db/README.md) - Learn about the schema and data loading
2. [Data Ingestion](ingestion/README.md) - Build data scraping pipeline (future)
3. [API Development](api/README.md) - Set up API server (future)
4. [Frontend](frontend/README.md) - Build Next.js application (future)