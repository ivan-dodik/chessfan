"""
Парсер для ruchess.ru (Рейтинг ФШР)
"""

import re
import json
from typing import Optional
from bs4 import BeautifulSoup

from utils import BaseParser, SessionManager


class RuChessPlayerParser(BaseParser):
    """
    Парсер страницы профиля шахматиста на ruchess.ru.
    
    URL пример: https://ratings.ruchess.ru/people/646647
    """
    
    def parse(self, html: str) -> dict:
        """Парсинг HTML и извлечение данных о игроке."""
        soup = BeautifulSoup(html, 'html.parser')
        
        result = {
            "name": None,
            "rus_id": None,
            "gender": None,
            "region_code": None,
            "region_name": None,
            "birth_year": None,
            "current_ratings": {
                "classical": {"rating": None, "rank": None, "total": None},
                "rapid": {"rating": None, "rank": None, "total": None},
                "blitz": {"rating": None, "rank": None, "total": None}
            },
            "rating_history": [],
            "last_tournaments": []
        }
        
        # Имя игрока
        name_h1 = soup.find('h1')
        if name_h1:
            name_text = name_h1.get_text(strip=True)
            # Формат: "Имя Фамилия" или "Имя Фамилия <small></small>"
            result["name"] = name_text.split('<')[0].strip()
        
        # Общая информация
        info_panel = soup.find('div', class_='panel', string='Общая информация')
        if not info_panel:
            # Попробуем найти по заголовку
            panel_title = soup.find('h3', class_='panel-title', string='Общая информация')
            if panel_title:
                info_panel = panel_title.find_parent('div', class_='panel')
        
        if info_panel:
            info_list = info_panel.find_next('ul', class_='list-group')
            if info_list:
                for li in info_list.find_all('li', class_='list-group-item'):
                    text = li.get_text(strip=True)
                    
                    if "ФШР ID" in text:
                        id_match = re.search(r'ФШР ID[:\s]*(\d+)', text)
                        if id_match:
                            result["rus_id"] = int(id_match.group(1))
                    
                    elif "Пол" in text:
                        gender_match = re.search(r'Пол[:\s]*(\w)', text)
                        if gender_match:
                            result["gender"] = gender_match.group(1)
                    
                    elif "Регион" in text:
                        region_match = re.search(r'Регион[:\s]*(\d+)\s*\((.+)\)', text)
                        if region_match:
                            result["region_code"] = region_match.group(1)
                            result["region_name"] = region_match.group(2).strip()
                    
                    elif "Год рождения" in text:
                        year_match = re.search(r'Год рождения[:\s]*(\d+)', text)
                        if year_match:
                            result["birth_year"] = int(year_match.group(1))
        
        # Текущий рейтинг
        rating_panel = soup.find('div', class_='panel', string='Текущий рейтинг')
        if not rating_panel:
            rating_title = soup.find('h3', class_='panel-title', string='Текущий рейтинг')
            if rating_title:
                rating_panel = rating_title.find_parent('div', class_='panel')
        
        if rating_panel:
            rating_list = rating_panel.find_next('ul', class_='list-group')
            if rating_list:
                for li in rating_list.find_all('li', class_='list-group-item'):
                    text = li.get_text(strip=True)
                    
                    # Формат: "Классические: рейтинг: 1299, место: 43366 из 232332"
                    if "Классические" in text:
                        result["current_ratings"]["classical"] = self._parse_rating_text(text)
                    elif "Быстрые" in text:
                        result["current_ratings"]["rapid"] = self._parse_rating_text(text)
                    elif "Блиц" in text:
                        result["current_ratings"]["blitz"] = self._parse_rating_text(text)
        
        # История рейтинга
        history_panel = soup.find('div', class_='panel', string='История рейтинга')
        if not history_panel:
            history_title = soup.find('h3', class_='panel-title', string='История рейтинга')
            if history_title:
                history_panel = history_title.find_parent('div', class_='panel')
        
        if history_panel:
            history_body = history_panel.find_next('div', class_='panel-body')
            if history_body:
                # Ищем script с данными для графика
                script = history_body.find('script')
                if script:
                    history_data = self._parse_rating_history(script.get_text())
                    result["rating_history"] = history_data
        
        # Последние турниры
        tournaments_panel = soup.find('div', class_='panel', string='Последние турниры')
        if not tournaments_panel:
            tournaments_title = soup.find('h3', class_='panel-title', string='Последние турниры')
            if tournaments_title:
                tournaments_panel = tournaments_title.find_parent('div', class_='panel')
        
        if tournaments_panel:
            tournaments_list = tournaments_panel.find_next('div', class_='list-group')
            if tournaments_list:
                for a in tournaments_list.find_all('a', class_='list-group-item'):
                    tournament = self._parse_tournament_link(a)
                    if tournament:
                        result["last_tournaments"].append(tournament)
        
        return result
    
    def _parse_rating_text(self, text: str) -> dict:
        """Парсинг текста с рейтингом."""
        result = {"rating": None, "rank": None, "total": None}
        
        # Извлечение рейтинга
        rating_match = re.search(r'рейтинг[:\s]*\d+', text)
        if rating_match:
            rating_value = re.search(r'\d+', rating_match.group())
            if rating_value:
                result["rating"] = int(rating_value.group())
        
        # Извлечение места
        rank_match = re.search(r'место[:\s]*(\d+)', text)
        if rank_match:
            result["rank"] = int(rank_match.group(1))
        
        # Извлечение общего количества
        total_match = re.search(r'из[:\s]*(\d+)', text)
        if total_match:
            result["total"] = int(total_match.group(1))
        
        return result
    
    def _parse_rating_history(self, script_text: str) -> list:
        """Парсинг истории рейтинга из JavaScript."""
        history = []
        
        # Ищем массив dataSource в JavaScript
        data_match = re.search(r'var\s+dataSource\s*=\s*(\[.*?\]);', script_text, re.DOTALL)
        if data_match:
            try:
                data_str = data_match.group(1)
                # Преобразуем JavaScript объекты в JSON-совместимый формат
                data_str = data_str.replace('new Date', '')
                data_str = re.sub(r'\{drs:', '{drs:', data_str)
                data_str = re.sub(r',\s*rrs:', ', "rrs":', data_str)
                data_str = re.sub(r',\s*drr:', ', "drr":', data_str)
                data_str = re.sub(r',\s*drb:', ', "drb":', data_str)
                data_str = re.sub(r',\s*rrr:', ', "rrr":', data_str)
                data_str = re.sub(r',\s*drf:', ', "drf":', data_str)
                data_str = re.sub(r',\s*rrf:', ', "rrf":', data_str)
                
                # Пытаемся распарсить как JSON
                data = json.loads(data_str)
                
                for item in data:
                    entry = {}
                    
                    # ФИДЕ стандарт
                    if 'dfs' in item and 'rfs' in item:
                        entry = {"date": item['dfs'], "rating": item['rfs'], "type": "fide_classical"}
                        history.append(entry)
                    
                    # ФИДЕ быстрые
                    if 'dfr' in item and 'rfr' in item:
                        entry = {"date": item['dfr'], "rating": item['rfr'], "type": "fide_rapid"}
                        history.append(entry)
                    
                    # ФИДЕ блиц
                    if 'dfb' in item and 'rfb' in item:
                        entry = {"date": item['dfb'], "rating": item['rfb'], "type": "fide_blitz"}
                        history.append(entry)
                    
                    # ФШР стандарт
                    if 'drs' in item and 'rrs' in item:
                        entry = {"date": item['drs'], "rating": item['rrs'], "type": "ruchess_classical"}
                        history.append(entry)
                    
                    # ФШР быстрые
                    if 'drr' in item and 'rrr' in item:
                        entry = {"date": item['drr'], "rating": item['rrr'], "type": "ruchess_rapid"}
                        history.append(entry)
                    
                    # ФШР блиц
                    if 'drb' in item and 'rrb' in item:
                        entry = {"date": item['drb'], "rating": item['rrb'], "type": "ruchess_blitz"}
                        history.append(entry)
                    
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error parsing rating history: {e}")
        
        return history
    
    def _parse_tournament_link(self, a_tag) -> Optional[dict]:
        """Парсинг ссылки на турнир."""
        href = a_tag.get('href')
        if not href:
            return None
        
        # Извлечение ID из URL
        id_match = re.search(r'/tournaments/(\d+)', href)
        if not id_match:
            return None
        
        tournament_id = int(id_match.group(1))
        name = a_tag.get_text(strip=True)
        
        return {
            "id": tournament_id,
            "name": name,
            "url": f"https://ratings.ruchess.ru/tournaments/{tournament_id}"
        }


class RuChessTournamentParser(BaseParser):
    """
    Парсер страницы турнира на ruchess.ru.
    
    URL пример: https://ratings.ruchess.ru/tournaments/241263
    """
    
    def parse(self, html: str) -> dict:
        """Парсинг HTML и извлечение данных о турнире."""
        soup = BeautifulSoup(html, 'html.parser')
        
        result = {
            "name": None,
            "location": None,
            "start_date": None,
            "end_date": None,
            "organizer": None,
            "director": None,
            "chief_arbiter": None,
            "time_control": None,
            "system": None,
            "rounds": None,
            "players_count": None,
            "rating_type": None,
            "federation": "RUS"
        }
        
        # Название турнира
        name_h1 = soup.find('h1')
        if name_h1:
            result["name"] = name_h1.get_text(strip=True)
        
        # Ищем таблицу с данными турнира
        info_table = soup.find('table', class_='table')
        if info_table:
            rows = info_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if "Место проведения" in label:
                        result["location"] = value
                    elif "Начало" in label:
                        result["start_date"] = value
                    elif "Окончание" in label:
                        result["end_date"] = value
                    elif "Организатор" in label:
                        result["organizer"] = value
                    elif "Турнирный директор" in label:
                        result["director"] = value
                    elif "Главный судья" in label or "Главный арбитр" in label:
                        result["chief_arbiter"] = value
                    elif "Контроль времени" in label:
                        result["time_control"] = value
                    elif "Система" in label:
                        result["system"] = value
                    elif "Туров" in label:
                        rounds_match = re.search(r'\d+', value)
                        if rounds_match:
                            result["rounds"] = int(rounds_match.group())
                    elif "Участников" in label:
                        players_match = re.search(r'\d+', value)
                        if players_match:
                            result["players_count"] = int(players_match.group())
                    elif "Рейтинг" in label:
                        result["rating_type"] = value
        
        return result