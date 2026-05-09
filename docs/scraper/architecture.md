# Архитектура парсера

## Общая схема

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Chessfan Scraper                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐ │
│  │   Parser Layer  │────▶│  Data Layer     │────▶│  Database Layer │ │
│  │   (Parsers)     │     │  (Transform)    │     │  (PostgreSQL)   │ │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘ │
│         │                        │                          │        │
│         ▼                        ▼                          ▼        │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐ │
│  │  BaseParser     │     │  CacheManager   │     │  Database       │ │
│  │  - fetch()      │     │  - get()        │     │  - connect()    │ │
│  │  - parse()      │     │  - set()        │     │  - upsert_*()   │ │
│  │  - parse_url()  │     │  - clear()      │     └─────────────────┘ │
│  └─────────────────┘     └─────────────────┘                          │
│         │                                                             │
│  ┌──────┴──────┐                                                      │
│  │             │                                                      │
│  ▼             ▼                                                      │
│  ┌─────────┐   ┌──────────┐                                          │
│  │ChessRes │   │RuChess   │                                          │
│  │Tournament│  │Player    │                                          │
│  │Round    │   │Tournament│                                          │
│  │Player   │   │          │                                          │
│  └─────────┘   └──────────┘                                          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Классы и их ответственность

### BaseParser

Базовый класс для всех парсеров. Предоставляет общий интерфейс:

```python
class BaseParser:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = sessionManager
    
    def fetch(self, url: str, use_cache: bool = True) -> str:
        """Получить HTML страницы."""
    
    def parse(self, html: str) -> dict:
        """Парсинг HTML и извлечение данных."""
    
    def parse_url(self, url: str, use_cache: bool = True) -> dict:
        """Получить и распарсить страницу."""
```

### CacheManager

Управление кэшем HTML-файлов:

- `_get_cache_key(url)` - генерация ключа из URL (MD5 хеш)
- `get(url)` - получение из кэша
- `set(url, html)` - сохранение в кэш
- `clear()` - очистка всего кэша

### SessionManager

Управление HTTP-сессией:

- `fetch(url, use_cache)` - получение HTML с retry-логикой
- Автоматические retry при ошибках (429, 500, 502, 503, 504)
- User-Agent для имитации браузера

### Парсеры chess-results.com

#### ChessResultsTournamentParser

Парсит страницу турнира (art=5):

**HTML-структура:**
```html
<h2>Название турнира</h2>
<table border="0" cellpadding="1" cellspacing="1">
  <tr><td>Организатор</td><td>...</td></tr>
  <tr><td>Федерация</td><td>...</td></tr>
  ...
</table>
```

**Извлекаемые данные:**
- Название
- Организатор
- Федерация
- Город
- Количество раундов
- Даты
- Контроль времени
- Система

#### ChessResultsRoundParser

Парсит страницу тура (art=2):

**HTML-структура:**
```html
<h3>1. Тур</h3>
<table class="CRs1">
  <tr class="CRng1b"><th>Bo.</th><th>White</th>...</tr>
  <tr class="CRng1"><td>1</td><td>Иванов</td>...</tr>
  ...
</table>
```

**Извлекаемые данные:**
- Номер тура
- Список партий с результатами

#### ChessResultsPlayerParser

Парсит страницу профиля игрока (art=9):

**HTML-структура:**
```html
<h2>Инфо игрока</h2>
<table class="CRs1">
  <tr><td>Имя</td><td>...</td></tr>
  ...
</table>
```

**Извлекаемые данные:**
- Имя
- ID
- Рейтинг
- Очки
- Место
- Список игр

### Парсеры ruchess.ru

#### RuChessPlayerParser

Парсит страницу профиля игрока:

**HTML-структура:**
```html
<h1>Имя игрока</h1>
<div class="panel" data="Общая информация">
  <ul class="list-group">
    <li>ФШР ID: 646647</li>
    ...
  </ul>
</div>
```

**Извлекаемые данные:**
- Имя
- ID
- Пол
- Регион
- Год рождения
- Текущий рейтинг (классический, быстрые, блиц)
- История рейтинга
- Последние турниры

## Поток данных

```
URL
  ↓
SessionManager.fetch()
  ↓
CacheManager.get() → (cache hit) → HTML
  ↓
CacheManager.set() → (cache miss) → HTTP request → HTML
  ↓
Parser.parse(html)
  ↓
BeautifulSoup parsing
  ↓
Structured data (dict)
  ↓
Database.upsert_*()
  ↓
PostgreSQL
```

## Обработка ошибок

1. **HTTP ошибки** - retry-логика в SessionManager
2. **Парсинг ошибки** - возврат None для отсутствующих данных
3. **База данных** - rollback при ошибках

## Расширяемость

Для добавления нового парсера:

1. Создать класс, наследующийся от `BaseParser`
2. Реализовать метод `parse(html: str) -> dict`
3. Добавить в `main.py` функцию обработки