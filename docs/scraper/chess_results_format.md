# Формат данных chess-results.com

## Структура URL

```
https://s{server}.chess-results.com/tnr{tournament_id}.aspx
  ?lan=11                    # Язык (11 = русский)
  &art={article_type}        # Тип страницы
  [&rd={round}]              # Номер тура (для страниц туров)
  [&fed={ federation}]       # Федерация (для профилей игроков)
  [&snr={seed}]              # Стартовый номер (для профилей игроков)
  [&turdet=YES]              # Детальная информация
  [&SNode=S0]                # Узел сервера
```

## Типы страниц

### 1. Информация о турнире (art=5)

**URL:** `https://s3.chess-results.com/tnr1393466.aspx?lan=11&art=5&SNode=S0`

**HTML-структура:**
```html
<h2>2026-3-ий Этап КУбка края памяти А.З.Боровика-C</h2>

<table border="0" cellpadding="1" cellspacing="1">
  <tr><td>Организатор(ы)</td><td>Фирсов Г.А.</td></tr>
  <tr><td>Федерация</td><td>Россия ( RUS )</td></tr>
  <tr><td>Турнирный директор</td><td>Фирсов Г.А.</td></tr>
  <tr><td>Главный арбитр</td><td>Степанов А.А.</td></tr>
  <tr><td>Заместитель главного судьи</td><td>Фирсов Г.А.</td></tr>
  <tr><td>Арбитр(ы)</td><td>Кашин О.В., Квачко О.А., Головина О.А., Фирсова О.В.</td></tr>
  <tr><td>Контроль времени (Rapid)</td><td>15'+10"</td></tr>
  <tr><td>Город</td><td><a href="...">Уссурийск</a></td></tr>
  <tr><td>Number of rounds</td><td>9</td></tr>
  <tr><td>Tournament type</td><td>Швейцарская система</td></tr>
  <tr><td>Расчет рейтинга</td><td> - </td></tr>
  <tr><td>Дата(ы)</td><td>2026/04/24 по 2026/04/25</td></tr>
  <tr><td>Рейт.-Ø / Average age</td><td>1205 / 9</td></tr>
</table>

<p class="CRsmall">
  Последнее обновление26.04.2026 06:02:14, 
  Автор/Последняя загрузка: Dvchess
</p>
```

**Извлекаемые данные:**
```json
{
  "name": "2026-3-ий Этап КУбка края памяти А.З.Боровика-C",
  "organizer": "Фирсов Г.А.",
  "federation": "Россия ( RUS )",
  "director": "Фирсов Г.А.",
  "chief_arbiter": "Степанов А.А.",
  "deputy_arbiter": "Фирсов Г.А.",
  "arbiters": "Кашин О.В., Квачко О.А., Головина О.А., Фирсова О.В.",
  "time_control": "15'+10\"",
  "city": "Уссурийск",
  "rounds": 9,
  "system": "Швейцарская система",
  "rating_system": "-",
  "start_date": "2026/04/24",
  "end_date": "2026/04/25",
  "avg_rating": 1205,
  "avg_age": 9,
  "last_update": "26.04.2026 06:02:14",
  "author": "Dvchess"
}
```

### 2. Результаты тура (art=2)

**URL:** `https://s3.chess-results.com/tnr1393466.aspx?lan=11&art=2&rd=1&turdet=YES&SNode=S0`

**HTML-структура:**
```html
<h3>1. Тур</h3>

<table class="CRs1" border="0" cellpadding="1" cellspacing="1">
  <tr class="CRng1b">
    <th class="CRc">Bo.</th>
    <th class="CRc">Ном.</th>
    <td class="CR">White</td>
    <th class="CRc">Рейт</th>
    <th class="CRc">Очки</th>
    <th class="CRc">Результат</th>
    <th class="CRc">Очки</th>
    <td class="CR">Black</td>
    <th class="CRc">Рейт</th>
    <th class="CRc">Ном.</th>
  </tr>
  <tr class="CRng2">
    <td class="CRc">48</td>
    <td class="CRc">1</td>
    <td class="RUS">
      <a href="...">Иванов, Иван Иванович</a>
    </td>
    <td class="CRc">1636</td>
    <td class="CRc">0</td>
    <td class="CRc">0 - 1</td>
    <td class="CRc">0</td>
    <td class="RUS">
      <a href="...">Петров, Петр Петрович</a>
    </td>
    <td class="CRc">1179</td>
    <td class="CRc">27</td>
  </tr>
  ...
</table>
```

**Извлекаемые данные:**
```json
{
  "round": 1,
  "games": [
    {
      "board": 48,
      "white_name": "Иванов, Иван Иванович",
      "white_rating": 1636,
      "white_seed": 1,
      "black_name": "Петров, Петр Петрович",
      "black_rating": 1179,
      "black_seed": 27,
      "result": "0 - 1",
      "white_score": 0.0,
      "black_score": 1.0
    }
  ]
}
```

### 3. Профиль игрока (art=9)

**URL:** `https://s1.chess-results.com/tnr1393466.aspx?lan=11&art=9&fed=RUS&turdet=YES&snr=1&SNode=S0`

**HTML-структура:**
```html
<h2>Инфо игрока</h2>

<table class="CRs1" border="0" cellpadding="1" cellspacing="1">
  <tr><td>Имя</td><td>Иванов, Иван Иванович</td></tr>
  <tr><td>Стартовое место</td><td>1</td></tr>
  <tr><td>Рейтинг</td><td>1636</td></tr>
  <tr><td>Нац.рейтинг</td><td>1636</td></tr>
  <tr><td>Междун. рейтинг</td><td>0</td></tr>
  <tr><td>Рейтинговый перфоманс</td><td>1536</td></tr>
  <tr><td>Очки</td><td>7</td></tr>
  <tr><td>Место</td><td>3</td></tr>
  <tr><td>Федерация</td><td>RUS</td></tr>
  <tr><td>Клуб/Город</td><td>Приморский край</td></tr>
  <tr><td>Идент.Номер</td><td>646647</td></tr>
  <tr><td>Год рождения</td><td>2010</td></tr>
</table>

<!-- Таблица с результатами игр -->
<table class="CRs1">
  <tr class="CRng1b">
    <th class="CRc">Тур</th>
    <th class="CRc">Bo.</th>
    <th class="CRc">Ст.ном.</th>
    <th class="CR">Имя</th>
    <th class="CRr">Рейт.</th>
    <th class="CR">ФЕД.</th>
    <th class="CR">Клуб/Город</th>
    <th class="CRc">Очки</th>
    <th class="CRc">Рез.</th>
  </tr>
  <tr class="CRng2 RUS">
    <td class="CRc">1</td>
    <td class="CRc">1</td>
    <td class="CRc">27</td>
    <td class="CR">Петров, Петр Петрович</td>
    <td class="CRr">1179</td>
    <td class="CR">RUS</td>
    <td class="CR">Приморский край</td>
    <td class="CRc">4</td>
    <td class="CR">
      <table><tr><td><div class="FarbewT"></div></td><td class="CR">0</td></tr></table>
    </td>
  </tr>
  ...
</table>
```

**Извлекаемые данные:**
```json
{
  "name": "Иванов, Иван Иванович",
  "seed": 1,
  "rating": 1636,
  "national_rating": 1636,
  "fide_rating": 0,
  "performance": 1536,
  "points": 7.0,
  "position": 3,
  "federation": "RUS",
  "club_city": "Приморский край",
  "rus_id": 646647,
  "birth_year": 2010,
  "games": [
    {
      "round": 1,
      "opponent_name": "Петров, Петр Петрович",
      "opponent_rating": 1179,
      "result": "0",
      "points": 4.0
    }
  ]
}
```

## Специальные случаи

### Bye (отдых)

В результатах тура может быть строка с "bye":

```html
<tr class="CRng1">
  <td class="CRc">75</td>
  <td class="CRc">54</td>
  <td class="CR"></td>
  <td class="RUS">Новиков, Максим Иванович</td>
  <td class="CRc">1085</td>
  <td class="CRc">0</td>
  <td class="CRc">1</td>
  <td class="CR" colspan=""></td>
  <td class="CR">bye</td>
  <td class="CRc">&nbsp;</td>
  <td></td>
</tr>
```

Это означает, что игрок получил очко без игры. В парсере такие строки должны быть пропущены.

### Отсутствующие данные

Если какая-то информация отсутствует, парсер возвращает `None` для соответствующего поля.