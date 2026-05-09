"""
Парсер для chess-results.com
"""

import re
from typing import Optional
from bs4 import BeautifulSoup

from utils import BaseParser, SessionManager


class ChessResultsTournamentParser(BaseParser):
    """
    Парсер страницы информации о турнире (art=5).
    
    URL пример: https://s3.chess-results.com/tnr1393466.aspx?lan=11&art=5&SNode=S0
    """
    
    def parse(self, html: str) -> dict:
        """Парсинг HTML и извлечение данных о турнире."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Название турнира
        title_h2 = soup.find('h2')
        tournament_name = title_h2.get_text(strip=True) if title_h2 else ""
        
        # Ищем таблицу с данными турнира
        # Сначала ищем div с классом defaultDialog, содержащий таблицу
        data_table = soup.find('table', border='0', cellpadding='1', cellspacing='1')
        
        result = {
            "name": tournament_name,
            "organizer": None,
            "federation": None,
            "director": None,
            "chief_arbiter": None,
            "deputy_arbiter": None,
            "arbiters": None,
            "time_control": None,
            "city": None,
            "rounds": None,
            "system": None,
            "rating_system": None,
            "start_date": None,
            "end_date": None,
            "avg_rating": None,
            "avg_age": None,
            "swiss_manager_url": None,
            "last_update": None,
            "author": None
        }
        
        if data_table:
            # Извлекаем данные из таблицы
            rows = data_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    # Очистка значения от лишних символов
                    value = re.sub(r'\s+', ' ', value)
                    
                    if "Организатор" in label:
                        result["organizer"] = value
                    elif "Федерация" in label:
                        result["federation"] = value
                    elif "Турнирный директор" in label:
                        result["director"] = value
                    elif "Главный арбитр" in label:
                        result["chief_arbiter"] = value
                    elif "Заместитель главного судьи" in label:
                        result["deputy_arbiter"] = value
                    elif "Арбитр" in label:
                        result["arbiters"] = value
                    elif "Контроль времени" in label:
                        result["time_control"] = value
                    elif "Город" in label:
                        # Извлекаем город из ссылки или текста
                        city_link = cells[1].find('a')
                        result["city"] = city_link.get_text(strip=True) if city_link else value
                    elif "Number of rounds" in label or "Количество раундов" in label:
                        result["rounds"] = int(value) if value.isdigit() else None
                    elif "Tournament type" in label or "Турнирный тип" in label:
                        result["system"] = value
                    elif "Расчет рейтинга" in label:
                        result["rating_system"] = value
                    elif "Дата" in label and "по" in value:
                        # Формат: 2026/04/24 по 2026/04/25
                        dates = value.split(' по ')
                        if len(dates) == 2:
                            result["start_date"] = dates[0].strip()
                            result["end_date"] = dates[1].strip()
                    elif "Рейт.-Ø" in label or "Average age" in label:
                        # Формат: 1205 / 9
                        parts = value.split(' / ')
                        if len(parts) == 2:
                            result["avg_rating"] = int(parts[0]) if parts[0].isdigit() else None
                            result["avg_age"] = int(parts[1]) if parts[1].isdigit() else None
                    elif "Программа" in label or "менеджер" in label:
                        # Ищем ссылку на Swiss-Manager файл
                        sm_link = cells[1].find('a', href=lambda x: x and 'swiss-manager' in x.lower())
                        if sm_link:
                            result["swiss_manager_url"] = sm_link.get('href')
        
        # Ищем дату последнего обновления
        last_update_elem = soup.find('p', class_='CRsmall')
        if last_update_elem:
            text = last_update_elem.get_text(strip=True)
            # Формат: Последнее обновление26.04.2026 06:02:14, Автор/Последняя загрузка: Dvchess
            update_match = re.search(r'Обновление(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})', text)
            if update_match:
                result["last_update"] = update_match.group(1)
            
            author_match = re.search(r'Автор/Последняя загрузка:\s*(\S+)', text)
            if author_match:
                result["author"] = author_match.group(1)
        
        return result


class ChessResultsRoundParser(BaseParser):
    """
    Парсер страницы с результатами тура (art=2).
    
    URL пример: https://s3.chess-results.com/tnr1393466.aspx?lan=11&art=2&rd=1&turdet=YES&SNode=S0
    """
    
    def parse(self, html: str) -> dict:
        """Парсинг HTML и извлечение данных о турах."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Извлекаем номер тура из заголовка
        round_header = soup.find('h3')
        round_number = 1
        if round_header:
            round_text = round_header.get_text(strip=True)
            round_match = re.search(r'(\d+)\.\s*Тур', round_text)
            if round_match:
                round_number = int(round_match.group(1))
        
        # Ищем таблицу с результатами
        results_table = soup.find('table', class_='CRs1')
        
        games = []
        
        if results_table:
            rows = results_table.find_all('tr')
            
            for row in rows:
                # Пропускаем заголовок
                if 'CRng1b' in row.get('class', []) or 'CRg1b' in row.get('class', []):
                    continue
                
                cells = row.find_all('td')
                
                # Проверяем, что у нас достаточно ячеек для партии
                if len(cells) >= 11:
                    try:
                        game = self._parse_game_row(cells)
                        if game:
                            games.append(game)
                    except (ValueError, IndexError) as e:
                        # Пропускаем строки с ошибками (например, bye)
                        continue
        
        return {
            "round": round_number,
            "games": games
        }
    
    def _parse_game_row(self, cells: list) -> Optional[dict]:
        """Парсинг одной строки с результатами партии."""
        # Структура ячеек:
        # 0: Bo. (номер доски)
        # 1: Ном. (стартовый номер белых)
        # 2: пустая
        # 3: White (имя белых)
        # 4: Рейт (рейтинг белых)
        # 5: Очки (очки белых до партии)
        # 6: Результат
        # 7: Очки (очки черных после партии)
        # 8: пустая
        # 9: Black (имя черных)
        # 10: Рейт (рейтинг черных)
        # 11: Ном. (стартовый номер черных)
        
        board = int(cells[0].get_text(strip=True)) if cells[0].get_text(strip=True).isdigit() else None
        
        # Имя белых
        white_name = self._get_player_name(cells[3])
        if not white_name:
            return None
        
        # Рейтинг белых
        white_rating = self._parse_rating(cells[4])
        
        # Результат
        result_cell = cells[6]
        result_text = result_cell.get_text(strip=True)
        
        # Очки белых после партии
        white_score_cell = cells[5]
        white_score = self._parse_score(white_score_cell.get_text(strip=True))
        
        # Очки черных после партии
        black_score_cell = cells[7]
        black_score = self._parse_score(black_score_cell.get_text(strip=True))
        
        # Имя черных
        black_name = self._get_player_name(cells[9])
        if not black_name:
            return None
        
        # Рейтинг черных
        black_rating = self._parse_rating(cells[10])
        
        # Стартовые номера
        white_seed = int(cells[1].get_text(strip=True)) if cells[1].get_text(strip=True).isdigit() else None
        black_seed = int(cells[11].get_text(strip=True)) if len(cells) > 11 and cells[11].get_text(strip=True).isdigit() else None
        
        return {
            "board": board,
            "white_name": white_name,
            "white_rating": white_rating,
            "white_seed": white_seed,
            "black_name": black_name,
            "black_rating": black_rating,
            "black_seed": black_seed,
            "result": result_text,
            "white_score": white_score,
            "black_score": black_score
        }
    
    def _get_player_name(self, cell) -> Optional[str]:
        """Извлечение имени игрока из ячейки."""
        link = cell.find('a')
        if link:
            return link.get_text(strip=True)
        return cell.get_text(strip=True) if cell.get_text(strip=True) not in ['bye', ''] else None
    
    def _parse_rating(self, cell) -> Optional[int]:
        """Парсинг рейтинга из ячейки."""
        text = cell.get_text(strip=True)
        if text and text.isdigit():
            return int(text)
        return None
    
    def _parse_score(self, text: str) -> Optional[float]:
        """Парсинг очков из текста."""
        if text and text.replace('.', '').isdigit():
            return float(text)
        return None


class ChessResultsPlayerParser(BaseParser):
    """
    Парсер страницы профиля игрока (art=9).
    
    URL пример: https://s1.chess-results.com/tnr1393466.aspx?lan=11&art=9&fed=RUS&turdet=YES&snr=1&SNode=S0
    """
    
    def parse(self, html: str) -> dict:
        """Парсинг HTML и извлечение данных о игроке."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем секцию с информацией об игроке
        info_section = soup.find('h2', string=re.compile(r'Инфо игрока|Инфо игрока'))
        
        result = {
            "name": None,
            "seed": None,
            "rating": None,
            "national_rating": None,
            "fide_rating": None,
            "performance": None,
            "points": None,
            "position": None,
            "federation": None,
            "club_city": None,
            "rus_id": None,
            "birth_year": None,
            "games": []
        }
        
        if info_section:
            # Ищем таблицу с информацией об игроке
            info_table = info_section.find_next('table', class_='CRs1')
            
            if info_table:
                rows = info_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        if "Имя" in label:
                            result["name"] = value
                        elif "Стартовое место" in label or "Старт. место" in label:
                            result["seed"] = int(value) if value.isdigit() else None
                        elif "Рейтинг" in label and "Нац" not in label:
                            result["rating"] = int(value) if value.isdigit() else None
                        elif "Нац.рейтинг" in label:
                            result["national_rating"] = int(value) if value.isdigit() else None
                        elif "Междун. рейтинг" in label or "FIDE" in label:
                            result["fide_rating"] = int(value) if value.isdigit() else None
                        elif "Рейтинговый перфоманс" in label:
                            result["performance"] = int(value) if value.isdigit() else None
                        elif "Очки" in label:
                            result["points"] = float(value) if value.replace('.', '').isdigit() else None
                        elif "Место" in label:
                            result["position"] = int(value) if value.isdigit() else None
                        elif "Федерация" in label:
                            result["federation"] = value
                        elif "Клуб" in label or "Город" in label:
                            result["club_city"] = value
                        elif "Идент" in label and "Номер" in label:
                            result["rus_id"] = int(value) if value.isdigit() else None
                        elif "Год рождения" in label:
                            result["birth_year"] = int(value) if value.isdigit() else None
        
        # Ищем таблицу с результатами игр
        games_table = soup.find('table', class_='CRs1')
        
        if games_table:
            # Ищем заголовок таблицы с играми
            header_row = games_table.find('tr', class_='CRng1b')
            if header_row:
                # Ищем строки с результатами игр
                game_rows = games_table.find_all('tr', class_=lambda x: x and ('CRng1' in x or 'CRng2' in x))
                
                for row in game_rows:
                    cells = row.find_all('td')
                    if len(cells) >= 10:
                        game = self._parse_game_result(cells)
                        if game:
                            result["games"].append(game)
        
        return result
    
    def _parse_game_result(self, cells: list) -> Optional[dict]:
        """Парсинг одной строки с результатом игры."""
        try:
            # Структура ячеек:
            # 0: Тур
            # 1: Bo.
            # 2: Ст.ном.
            # 3: пустая
            # 4: Имя
            # 5: Рейт.
            # 6: ФЕД.
            # 7: Клуб/Город
            # 8: Очки
            # 9: Рез.
            
            round_num = int(cells[0].get_text(strip=True)) if cells[0].get_text(strip=True).isdigit() else None
            
            opponent_name = cells[4].get_text(strip=True)
            opponent_rating = self._parse_rating(cells[5])
            
            # Результат
            result_cell = cells[9]
            result_text = self._parse_result(result_cell)
            
            # Очки после игры
            points_cell = cells[8]
            points = self._parse_score(points_cell.get_text(strip=True))
            
            return {
                "round": round_num,
                "opponent_name": opponent_name,
                "opponent_rating": opponent_rating,
                "result": result_text,
                "points": points
            }
        except (ValueError, IndexError):
            return None
    
    def _parse_rating(self, cell) -> Optional[int]:
        """Парсинг рейтинга из ячейки."""
        text = cell.get_text(strip=True)
        if text and text.isdigit():
            return int(text)
        return None
    
    def _parse_result(self, cell) -> Optional[str]:
        """Парсинг результата из ячейки."""
        # Результат может быть вложенным в таблицу
        table = cell.find('table')
        if table:
            result_cell = table.find('td')
            if result_cell:
                return result_cell.get_text(strip=True)
        return cell.get_text(strip=True)
    
    def _parse_score(self, text: str) -> Optional[float]:
        """Парсинг очков из текста."""
        if text and text.replace('.', '').isdigit():
            return float(text)
        return None