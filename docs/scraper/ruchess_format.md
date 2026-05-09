# Формат данных ruchess.ru

## Структура URL

```
https://ratings.ruchess.ru/people/{player_id}
https://ratings.ruchess.ru/tournaments/{tournament_id}
```

## Типы страниц

### 1. Профиль игрока

**URL:** `https://ratings.ruchess.ru/people/646647`

**HTML-структура:**

#### Общая информация
```html
<h1>Иванов Иван Иванович</h1>

<div class="panel panel-default">
  <div class="panel-heading"><h3 class="panel-title">Общая информация</h3></div>
  <ul class="list-group">
    <li class="list-group-item"><strong>ФШР ID</strong>: 646647</li>
    <li class="list-group-item"><strong>Пол</strong>: М</li>
    <li class="list-group-item">
      <strong>Регион</strong>: 25 (Приморский край)
    </li>
    <li class="list-group-item"><strong>Год рождения</strong>: 2010</li>
  </ul>
</div>
```

#### Текущий рейтинг
```html
<div class="panel panel-default">
  <div class="panel-heading"><h3 class="panel-title">Текущий рейтинг</h3></div>
  <ul class="list-group">
    <li class="list-group-item">
      <strong><span class="text-primary">Классические:</span></strong>
      рейтинг: <b>1299</b>, место: <b>43366</b> из <b>232332</b>
    </li>
    <li class="list-group-item">
      <strong><span class="text-success">Быстрые:</span></strong>
      рейтинг: <b>1622</b>, место: <b>17473</b> из <b>277884</b>
    </li>
    <li class="list-group-item">
      <strong><span class="text-danger">Блиц:</span></strong>
      рейтинг: <b>1207</b>, место: <b>56531</b> из <b>111498</b>
    </li>
  </ul>
</div>
```

#### История рейтинга
```html
<div class="panel panel-default">
  <div class="panel-heading"><h3 class="panel-title">История рейтинга</h3></div>
  <div class="panel-body">
    <div id="rating-plot">
      <!-- SVG график -->
    </div>
    <script>
      var dataSource = [
        {drs: new Date(2025,1,16), rrs: 1020},
        {drs: new Date(2025,3,1), rrs: 1043},
        {drr: new Date(2025,0,19), rrr: 1000},
        {drr: new Date(2025,2,16), rrr: 1003},
        {drb: new Date(2025,7,14), rrb: 1205},
        ...
      ];
    </script>
  </div>
</div>
```

**Примечание:** История рейтинга извлекается из JavaScript массива `dataSource`. Формат данных:
- `drs` / `rrs` - дата и рейтинг для классических шахмат
- `drr` / `rrr` - дата и рейтинг для быстрых шахмат
- `drb` / `rrb` - дата и рейтинг для блица
- `dfs` / `rfs` - дата и рейтинг ФИДЕ для классических
- `dfr` / `rfr` - дата и рейтинг ФИДЕ для быстрых
- `dfb` / `rfb` - дата и рейтинг ФИДЕ для блица

#### Последние турниры
```html
<div class="panel panel-default">
  <div class="panel-heading"><h3 class="panel-title">Последние турниры</h3></div>
  <div class="list-group">
    <a class="list-group-item" href="/tournaments/242039">
      Октрытый чемпионат г.Владивостока по шахматам. Турнир — С.
    </a>
    <a class="list-group-item" href="/tournaments/241263">
      Турнир памяти А.З.Боровика — 2026-3-ий Этап Кубка Приморского края памяти А.З.Боровика-C
    </a>
  </div>
</div>
```

**Извлекаемые данные:**
```json
{
  "name": "Иванов Иван Иванович",
  "rus_id": 646647,
  "gender": "M",
  "region_code": "25",
  "region_name": "Приморский край",
  "birth_year": 2010,
  "current_ratings": {
    "classical": {
      "rating": 1299,
      "rank": 43366,
      "total": 232332
    },
    "rapid": {
      "rating": 1622,
      "rank": 17473,
      "total": 277884
    },
    "blitz": {
      "rating": 1207,
      "rank": 56531,
      "total": 111498
    }
  },
  "rating_history": [
    {
      "date": "2025-02-16",
      "rating": 1020,
      "type": "ruchess_classical"
    },
    {
      "date": "2025-04-01",
      "rating": 1043,
      "type": "ruchess_classical"
    },
    {
      "date": "2025-01-19",
      "rating": 1000,
      "type": "ruchess_rapid"
    },
    {
      "date": "2025-08-14",
      "rating": 1205,
      "type": "ruchess_blitz"
    }
  ],
  "last_tournaments": [
    {
      "id": 242039,
      "name": "Октрытый чемпионат г.Владивостока по шахматам. Турнир — С.",
      "url": "https://ratings.ruchess.ru/tournaments/242039"
    },
    {
      "id": 241263,
      "name": "Турнир памяти А.З.Боровика — 2026-3-ий Этап Кубка Приморского края памяти А.З.Боровика-C",
      "url": "https://ratings.ruchess.ru/tournaments/241263"
    }
  ]
}
```

### 2. Страница турнира

**URL:** `https://ratings.ruchess.ru/tournaments/241263`

**HTML-структура:**
```html
<h1>Турнир памяти А.З.Боровика — 2026-3-ий Этап Кубка Приморского края памяти А.З.Боровика-C</h1>

<table class="table">
  <tr>
    <th>Место проведения:</th>
    <td>Уссурийск</td>
  </tr>
  <tr>
    <th>Начало:</th>
    <td>24.04.2026</td>
  </tr>
  <tr>
    <th>Окончание:</th>
    <td>25.04.2026</td>
  </tr>
  <tr>
    <th>Организатор:</th>
    <td>Фирсов Г.А.</td>
  </tr>
  <tr>
    <th>Турнирный директор:</th>
    <td>Фирсов Г.А.</td>
  </tr>
  <tr>
    <th>Главный судья:</th>
    <td>Степанов А.А.</td>
  </tr>
  <tr>
    <th>Контроль времени:</th>
    <td>15'+10"</td>
  </tr>
  <tr>
    <th>Система:</th>
    <td>Швейцарская система</td>
  </tr>
  <tr>
    <th>Туров:</th>
    <td>9</td>
  </tr>
  <tr>
    <th>Участников:</th>
    <td>55</td>
  </tr>
  <tr>
    <th>Рейтинг:</th>
    <td>ФШР</td>
  </tr>
</table>
```

**Извлекаемые данные:**
```json
{
  "name": "Турнир памяти А.З.Боровика — 2026-3-ий Этап Кубка Приморского края памяти А.З.Боровика-C",
  "location": "Уссурийск",
  "start_date": "24.04.2026",
  "end_date": "25.04.2026",
  "organizer": "Фирсов Г.А.",
  "director": "Фирсов Г.А.",
  "chief_arbiter": "Степанов А.А.",
  "time_control": "15'+10\"",
  "system": "Швейцарская система",
  "rounds": 9,
  "players_count": 55,
  "rating_type": "ФШР",
  "federation": "RUS"
}
```

## Типы рейтингов

| Код | Название | Описание |
|-----|----------|----------|
| `ruchess_classical` | ФШР классические | Классические шахматы |
| `ruchess_rapid` | ФШР быстрые | Быстрые шахматы |
| `ruchess_blitz` | ФШР блиц | Блиц |
| `fide_classical` | ФИДЕ классические | Классические шахматы (FIDE) |
| `fide_rapid` | ФИДЕ быстрые | Быстрые шахматы (FIDE) |
| `fide_blitz` | ФИДЕ блиц | Блиц (FIDE) |

## Специальные случаи

### Отсутствующие данные

Если какая-то информация отсутствует, парсер возвращает `None` для соответствующего поля.

### Пустая история рейтинга

Если у игрока нет истории рейтинга, поле `rating_history` будет пустым массивом.

### Отсутствующие турниры

Если у игрока нет турниров, поле `last_tournaments` будет пустым массивом.