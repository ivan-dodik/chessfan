# Project Brief: Chessfan

## Overview
Chessfan is a chess tournaments and player stats monitoring service. The project aims to help chess fans track their favorite players' games on offline tournaments, monitor rating changes, and receive notifications about results.

## Core Requirements
- Monitor chess tournaments (primarily offline events)
- Track player ratings and rating history
- Collect and display tournament statistics
- Provide live updates and notifications via pg_notify
- Support rating history tracking

## Data Sources
- chess-results.com (tournament results and player information)
- Russian Chess Federation website (player ratings)

## Technical Constraints
- Database: PostgreSQL 13+
- Data ingestion via external programs (not real-time)
- Ratings updated only after tournament completion
- No PGN notation in MVP
- No exact game start/end times (only tournament dates)
- Single score field in games table (white's points only)
- rus_id instead of fide_id for Russian Federation ID

## MVP Scope
- Player profiles with rating history
- Tournament tracking and standings
- Live tournament table updates
- Player vs player statistics
- Rating history tracking

## Database Schema (MVP)
- **6 Tables**: players, tournaments, tournament_players, games, player_ratings, tournament_standings
- **11 Indexes**: For query optimization
- **3 Views**: v_active_tournament_table, v_player_profile, v_player_rating_history
- **1 Trigger**: pg_notify for live game result notifications

## Current Status
**Database Implementation Complete** - Database schema designed and documented in docs/db/ directory.
**Docker Deployment Ready** - PostgreSQL configured via Docker Compose.

## Files
- docs/db/README.md - Database setup guide
- docs/db/schema.md - Database schema documentation
- docs/db/sql/create.sql - SQL script to create database
- docs/db/views.md - Database views documentation
- docs/db/triggers.md - Triggers and notifications documentation
- docs/deployment/docker.md - Docker deployment guide
- docker-compose.yml - Docker Compose configuration
- .env.example - Environment variables example
