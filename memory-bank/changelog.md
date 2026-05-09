# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Timestamp format (YYYY-MM-DD HH:MM) for CHANGES.md entries
- Rules for adding new entries (always at end of file)
- Inverted timestamps in CHANGES.md for chronological order

### Added
- Initial project structure
- Memory bank documentation

## [2026-05-10 04:05] - Documentation Updates

### Added
- Updated .clinerules/update_prompts.md with timestamp format and new entry rules
- Updated CHANGES.md with timestamps and inverted chronological order
- Added current changes to CHANGES.md

### Changed
- CHANGES.md format: YYYY-MM-DD HH:MM instead of YYYY-MM-DD only
- CHANGES.md order: chronological (newest at bottom)

## [2026-05-10] - Milestone 1: Database Ready

### Added
- Database schema design (6 tables, 11 indexes, 3 views, 1 trigger)
- Docker Compose configuration for PostgreSQL 15
- Automated deployment script (deploy.sh)
- Database verification guide (docs/deployment/verify.md)
- Sample data script (docs/db/sql/sample_data.sql)
- Python scraper for chess-results.com and ruchess.ru
- Data obfuscation for privacy

### Changed
- Updated project documentation structure

## [2026-05-10] - Scraper Development

### Added
- BaseParser, CacheManager, SessionManager classes
- ChessResultsTournamentParser, ChessResultsRoundParser, ChessResultsPlayerParser
- RuChessPlayerParser, RuChessTournamentParser
- Database class for PostgreSQL integration
- CLI interface for running parsers
- Comprehensive documentation in docs/scraper/

## [2026-05-10] - Database Deployment Script

### Added
- deploy.sh - Main deployment script
- docs/deployment/verify.md - Comprehensive verification guide

## [2026-05-10] - Root README.md Update

### Added
- Project overview section
- Quick start section with deployment instructions
- Documentation table with links

## [2026-05-10] - Scraper Data Obfuscation

### Changed
- Replaced real player names with fictional names (55 players)
- Replaced real birth years with fictional years (shifted by -6 years)
- Updated documentation with obfuscated data

## [2026-05-10] - Database Schema

### Added
- 6 tables: players, tournaments, tournament_players, games, player_ratings, tournament_standings
- 11 indexes for query optimization
- 3 views: v_active_tournament_table, v_player_profile, v_player_rating_history
- 1 pg_notify trigger for live game result notifications

## [2026-05-10] - Docker Compose for PostgreSQL

### Added
- docker-compose.yml with PostgreSQL 15 configuration
- .env.example with environment variables
- docs/deployment/docker.md with deployment guide

## [2026-05-10] - Database Documentation

### Added
- docs/db/README.md - Database setup guide
- docs/db/schema.md - Database schema documentation
- docs/db/views.md - Database views documentation
- docs/db/triggers.md - Triggers and notifications documentation
- docs/db/sql/create.sql - SQL script to create database