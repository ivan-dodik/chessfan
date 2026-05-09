# Project Brief: Chessfan

## Overview
Chessfan is a chess tournaments and player stats monitoring service. The project aims to help chess fans track their favorite players' games on offline tournaments, monitor rating changes, and receive notifications about results.

## Core Requirements
- Monitor chess tournaments (primarily offline events)
- Track player ratings and rating history
- Collect and display tournament statistics
- Provide live updates and notifications
- Support "what-if" analysis for tournament outcomes

## Data Sources
- chess-results.com (tournament results and player information)
- Russian Chess Federation website (player ratings)

## Technical Constraints
- Database: PostgreSQL
- Data ingestion via external programs (not real-time)
- Ratings updated only after tournament completion
- No PGN notation in MVP
- No exact game start/end times (only tournament dates)

## MVP Scope
- Player profiles with rating history
- Tournament tracking and standings
- Live tournament table updates
- Player vs player statistics
- Rating change projections

## Current Status
Project is in initial planning phase. No source code has been written yet.