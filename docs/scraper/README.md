# Парсер шахматных данных (Chessfan Scraper)

Пакет для парсинга данных о шахматных турнирах с chess-results.com и рейтингов с ruchess.ru.

## Структура проекта

```
scraper/
├── src/
│   ├── __init__.py          # Инициализация пакета
│   ├── utils.py             # Утилиты (кэш, сессия, базовый класс)
│   ├── chess_results_parser.py  # Парсер chess-results.com
│   ├── ruchess_parser.py    # Парсер ruchess.ru
│   └── database.py          # Интеграция с PostgreSQL
├── data/                    # Кэш HTML-файлов
├── html_samples/            # Примеры HTML
├── main.py                  # Основной скрипт
├── requirements.txt         # Зависимости
└── tests/                   # Тесты

docs/scraper/
├── README.md                # Этот файл
├── architecture.md          # Архитектура парсера
├── chess_results_format.md  # Формат данных chess-results.com
└── ruchess_format.md        # Формат данных ruchess.ru
```

## Примеры данных

Все примеры данных в документации и HTML-файлах содержат вымышленные имена игроков для защиты конфиденциальности.

**Вымышленные имена:** Иванов Иван Иванович, Петров Петр Петрович, Сидоров Сидор Сидорович, Кузнецов Алексей Сергеевич, Попов Максим Викторович, Смирнова Анна Дмитриевна, Васильев Даниил Андреевич, Михайлов Артём Евгеньевич, Новиков Илья Олегович, Соколов Артем Игоревич, Морозов Семен Максимович, Воробьев Михаил Сергеевич, Волков Иван Алексеевич, Миронов Даниил Павлович, Алексеева Екатерина Ивановна, Федоров Максим Олегович, Андреев Иван Сергеевич, Николаев Артём Викторович, Павлов Семен Иванович, Семенов Михаил Андреевич, Егоров Даниил Олегович, Максимов Иван Михайлович, Никитин Максим Сергеевич, Орлова Анна Ивановна, Козлова Екатерина Сергеевна, Медведев Артём Алексеевич, Борисов Даниил Олегович, Соловьев Максим Иванович, Волков Илья Максимович, Морозов Даниил Андреевич, Попов Артём Олегович, Смирнов Максим Иванович, Васильев Даниил Сергеевич, Новиков Илья Олегович, Федоров Артём Михайлович, Андреев Даниил Олегович, Воробьев Максим Иванович, Павлов Артём Сергеевич, Миронов Даниил Олегович, Соколова Анна Ивановна, Волков Максим Андреевич, Михайлов Даниил Сергеевич, Орлова Екатерина Ивановна, Козлова Анна Михайловна, Борисов Максим Иванович, Воробьев Даниил Олегович, Смирнов Максим Сергеевич, Новиков Артём Иванович, Федоров Даниил Олегович, Андреев Максим Иванович, Павлова Анна Сергеевна, Васильев Даниил Михайлович, Морозов Артём Олегович, Новиков Максим Иванович, Соколов Даниил Сергеевич.

**Вымышленные годы рождения:** 2010, 2009, 2008, 2007, 2006, 2005, 2004, 2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994, 1993, 1992, 1991, 1990

## Установка

```bash
cd scraper
pip install -r requirements.txt
```

### Зависимости

- `requests` - HTTP-запросы
- `beautifulsoup4` - парсинг HTML
- `psycopg2-binary` - PostgreSQL драйвер
- `python-dotenv` - управление переменными окружения

## Использование

### Командная строка

```bash
# Парсинг страницы турнира
python main.py -t tournament -i "html_samples/Chess-Results Server Chess-results.com - 2026-3-ий Этап Кубка края памяти А.З.Боровика-C.html"

# Парсинг страницы тура
python main.py -t round -i "html_samples/Chess-Results Server Chess-results.com - 2026-3-ий Этап Кубка края памяти А.З.Боровика-C Тур 1.html"

# Парсинг профиля игрока (chess-results)
python main.py -t player -i "html_samples/Chess-Results Server Chess-results.com - 2026-3-ий Этап Кубка края памяти А.З.Боровика-C профиль игрока.html"

# Парсинг профиля игрока (ruchess)
python main.py -t ruchess -i "html_samples/Профиль шахматиста — Иванов Иван Иванович _ Рейтинг ФШР.html"
```

### Программное использование

```python
from scraper.src.utils import CacheManager, SessionManager
from scraper.src.chess_results_parser import ChessResultsTournamentParser
from scraper.src.ruchess_parser import RuChessPlayerParser

# Создание менеджера сессии
cache = CacheManager()
session = SessionManager(cache)

# Парсинг турнира
parser = ChessResultsTournamentParser(session)
data = parser.parse_url("https://s3.chess-results.com/tnr1393466.aspx?lan=11&art=5")

# Парсинг профиля игрока
parser = RuChessPlayerParser(session)
data = parser.parse_url("https://ratings.ruchess.ru/people/646647")
```

## Архитектура

### Базовый класс

Все парсеры наследуются от `BaseParser`, который предоставляет:
- `fetch(url)` - получение HTML с кэшированием
- `parse(html)` - парсинг HTML
- `parse_url(url)` - получение и парсинг страницы

### Кэширование

HTML-файлы кэшируются в папке `data/` для избежания повторных запросов к серверам.

### База данных

Интеграция с PostgreSQL через класс `Database`:
- `upsert_player()` - вставка/обновление игрока
- `upsert_tournament()` - вставка/обновление турнира
- `upsert_game()` - вставка/обновление игры
- `upsert_player_rating()` - вставка/обновление рейтинга
- `upsert_tournament_standings()` - вставка/обновление позиции в турнире

## Типы парсеров

### ChessResultsTournamentParser

Парсит страницу информации о турнире (art=5).

**Вход:** `https://s3.chess-results.com/tnr1393466.aspx?lan=11&art=5&SNode=S0`

**Выход:**
```json
{
  "name": "Название турнира",
  "organizer": "Организатор",
  "federation": "RUS",
  "city": "Город",
  "rounds": 9,
  "start_date": "2026/04/24",
  "end_date": "2026/04/25",
  "time_control": "15'+10\"",
  "system": "Швейцарская система"
}
```

### ChessResultsRoundParser

Парсит страницу с результатами тура (art=2).

**Вход:** `https://s3.chess-results.com/tnr1393466.aspx?lan=11&art=2&rd=1&turdet=YES&SNode=S0`

**Выход:**
```json
{
  "round": 1,
  "games": [
    {
      "board": 1,
      "white_name": "Иванов Иван",
      "white_rating": 1500,
      "black_name": "Петров Петр",
      "black_rating": 1400,
      "result": "1-0",
      "white_score": 1.0,
      "black_score": 0.0
    }
  ]
}
```

### ChessResultsPlayerParser

Парсит страницу профиля игрока (art=9).

**Вход:** `https://s1.chess-results.com/tnr1393466.aspx?lan=11&art=9&fed=RUS&turdet=YES&snr=1&SNode=S0`

**Выход:**
```json
{
  "name": "Иванов Иван",
  "rus_id": 123456,
  "rating": 1500,
  "points": 7.0,
  "position": 3,
  "games": [...]
}
```

### RuChessPlayerParser

Парсит страницу профиля игрока на ruchess.ru.

**Вход:** `https://ratings.ruchess.ru/people/646647`

**Выход:**
```json
{
  "name": "Иванов Иван",
  "rus_id": 646647,
  "gender": "M",
  "region_name": "Приморский край",
  "birth_year": 2016,
  "current_ratings": {
    "classical": {"rating": 1299, "rank": 43366, "total": 232332},
    "rapid": {"rating": 1622, "rank": 17473, "total": 277884},
    "blitz": {"rating": 1207, "rank": 56531, "total": 111498}
  },
  "rating_history": [...],
  "last_tournaments": [...]
}
```

## Интеграция с базой данных

```python
from scraper.src.database import Database

db = Database()
db.connect()

# Вставка игрока
player_id = db.upsert_player({
    "rus_id": 646647,
    "name": "Иванов Иван Иванович",
    "gender": "M",
    "birth_year": 2010,
    "city": "Приморский край"
})

# Вставка турнира
tournament_id = db.upsert_tournament({
    "name": "2026-3-ий Этап КУбка края памяти А.З.Боровика-C",
    "location": "Уссурийск",
    "start_date": "2026-04-24",
    "end_date": "2026-04-25"
})

# Вставка игры
game_id = db.upsert_game({
    "tournament_id": tournament_id,
    "round": 1,
    "white_player_id": player_id,
    "black_player_id": other_player_id,
    "score": 1.0
})

db.close()
```

## Логирование

Используется стандартная библиотека `logging`. Уровень логирования можно изменить:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Кэширование

Кэш хранится в папке `data/` в виде HTML-файлов с именами в формате MD5 хеша URL.

Очистка кэша:
```python
from scraper.src.utils import CacheManager

cache = CacheManager()
cache.clear()
```

## Обработка ошибок

Все парсеры обрабатывают ошибки парсинга и возвращают `None` для отсутствующих данных.