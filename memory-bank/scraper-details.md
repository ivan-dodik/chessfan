# Scraper Details

## Architecture

### Base Classes

#### BaseParser
Abstract base class for all parsers with methods:
- `fetch(url)` - Fetch HTML with retry logic
- `parse(html)` - Parse HTML content
- `parse_url(url)` - Parse URL and extract parameters

#### CacheManager
Manages HTML caching with MD5 hash keys:
- `get_cache_key(url)` - Generate cache key from URL
- `load_cache(key)` - Load cached HTML
- `save_cache(key, html)` - Save HTML to cache

#### SessionManager
Manages HTTP sessions with retry logic:
- `get_session()` - Get session with retry configuration
- `fetch_with_retry(url)` - Fetch with automatic retries

### Parsers

#### ChessResultsTournamentParser
Parses tournament info page (art=5):
- Tournament name, location, dates
- Number of rounds
- Player count

#### ChessResultsRoundParser
Parses round results page (art=2):
- Game results for all pairs
- Player names and IDs
- Round number

#### ChessResultsPlayerParser
Parses player profile page (art=9):
- Player name, ID, gender, birth year
- Rating history
- Tournament participation

#### RuChessPlayerParser
Parses Russian chess federation player profile:
- Player name, ID, gender, region, birth year
- All rating types (FIDE, Russian, etc.)
- Rating history from JavaScript dataSource array
- Recent tournaments

#### RuChessTournamentParser
Parses Russian chess federation tournament page:
- Tournament information
- Player list
- Results

## Data Sources

### chess-results.com
- Tournament info: `art=5`
- Round results: `art=2`
- Player profile: `art=9`
- Uses ASP.NET WebForms with __doPostBack

### ruchess.ru
- Player profile: `/people/{id}`
- Tournament page: `/tour/{id}`
- Uses Bootstrap with DevExpress charts
- Rating history stored in JavaScript dataSource array

## HTML Caching

### Cache Key Format
```
MD5(url)
```

### Cache Location
```
scraper/html_cache/{cache_key}.html
```

### Cache Invalidation
- Check if cached file exists
- Verify file is not stale (optional: add timestamp check)

## HTTP Retry Logic

### Configuration
- Max retries: 3
- Delay between retries: 2 seconds
- Timeout: 30 seconds

## Database Integration

### Upsert Operations
- Players: UPSERT on rus_id
- Tournaments: UPSERT on name + start_date + end_date
- Games: INSERT with ON CONFLICT DO NOTHING
- Ratings: UPSERT on player_id + rating_date
- Standings: UPSERT on tournament_id + player_id + round

### Connection String
```
PGPASSWORD=chessfan123 psql -h localhost -p 5432 -U chessfan -d chessfan
```

## CLI Interface

### Usage
```bash
python -m scraper.main [parser] [url]
```

### Parsers
- `tournament` - ChessResultsTournamentParser
- `round` - ChessResultsRoundParser
- `player` - ChessResultsPlayerParser
- `ruchess_player` - RuChessPlayerParser
- `ruchess_tournament` - RuChessTournamentParser

## Testing

### HTML Samples
Located in `scraper/html_samples/`:
- Tournament pages
- Round pages
- Player profile pages

### Verification
- Parser runs without errors
- Data extracted correctly
- Database records created/updated