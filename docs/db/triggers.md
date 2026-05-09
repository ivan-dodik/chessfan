# Triggers and Notifications

## Overview

This document describes the triggers and notification system in Chessfan MVP.

## Live Notifications

The database sends real-time notifications when game results change using PostgreSQL's `pg_notify` feature.

### Notification Channel

**Channel name:** `game_result_changes`

**Payload format:** JSON

### Notification Events

| Event | Description |
|-------|-------------|
| `game_created` | A new game was inserted |
| `game_updated` | An existing game was updated |
| `game_deleted` | A game was deleted |

### Payload Structure

```json
{
  "event": "game_created",
  "game_id": 123,
  "tournament_id": 5,
  "tournament_name": "Moscow Open 2024",
  "round": 3,
  "white_player_id": 10,
  "black_player_id": 15,
  "score": 1,
  "timestamp": "2024-05-10T00:00:00+00:00"
}
```

## Trigger

### Trigger Name

`trg_notify_game_result_change`

### Trigger Function

`notify_game_result_change()`

### Trigger Events

- AFTER INSERT
- AFTER UPDATE  
- AFTER DELETE

### Table

`games`

## Usage Examples

### Subscribing to Notifications (psql)

```sql
-- Connect to database and subscribe
LISTEN game_result_changes;

-- Wait for notifications (press Ctrl+C to cancel)
-- When a game changes, you'll see:
-- Asynchronous notification "game_result_changes" with payload {"event":"...",...}
```

### Subscribing to Notifications (Python)

```python
import psycopg2
import json

conn = psycopg2.connect("dbname=chessfan user=postgres")
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

cur = conn.cursor()
cur.execute("LISTEN game_result_changes")

print("Waiting for notifications...")
while True:
    if conn.notifies:
        for notify in conn.notifies:
            payload = json.loads(notify.payload)
            print(f"Event: {payload['event']}")
            print(f"Tournament: {payload['tournament_name']}")
            print(f"Round: {payload['round']}")
            print(f"White: {payload['white_player_id']}, Black: {payload['black_player_id']}")
            print(f"Score: {payload['score']}")
        conn.notifies = []
    conn.poll()
```

### Subscribing to Notifications (Node.js)

```javascript
const { Client } = require('pg');

const client = new Client({
  connectionString: 'postgresql://postgres@localhost/chessfan'
});

async function start() {
  await client.connect();
  
  await client.query('LISTEN game_result_changes');
  
  client.on('notification', (msg) => {
    const payload = JSON.parse(msg.payload);
    console.log(`Event: ${payload.event}`);
    console.log(`Tournament: ${payload.tournament_name}`);
    console.log(`Round: ${payload.round}`);
    console.log(`Score: ${payload.score}`);
  });
}

start();
```

## Testing Notifications

1. Open psql and run: `LISTEN game_result_changes;`
2. In another psql session, insert a game:
```sql
INSERT INTO games (tournament_id, round, white_player_id, black_player_id, score)
VALUES (1, 1, 1, 2, 1);
```
3. You should see the notification in the first session

## Troubleshooting

### No notifications received?

1. Check PostgreSQL configuration:
```sql
SHOW listen_addresses;
SHOW port;
```

2. Ensure you're connected to the same database

3. Verify the trigger exists:
```sql
SELECT * FROM pg_trigger WHERE tgname = 'trg_notify_game_result_change';
```

4. Check the function exists:
```sql
SELECT * FROM pg_proc WHERE proname = 'notify_game_result_change';