#!/usr/bin/env python3
"""
Основной скрипт для запуска парсера.
"""

import os
import sys
import argparse
from pathlib import Path

# Добавляем путь к модулям
scraper_path = Path(__file__).parent
sys.path.insert(0, str(scraper_path / "src"))

from utils import CacheManager, SessionManager
from chess_results_parser import (
    ChessResultsTournamentParser,
    ChessResultsRoundParser,
    ChessResultsPlayerParser
)
from ruchess_parser import RuChessPlayerParser
from database import Database


def parse_tournament(html_file: str, output: str = None):
    """Парсинг страницы информации о турнире."""
    parser = ChessResultsTournamentParser(SessionManager(CacheManager()))
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    data = parser.parse(html)
    
    if output:
        import json
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Название: {data['name']}")
    print(f"Организатор: {data['organizer']}")
    print(f"Федерация: {data['federation']}")
    print(f"Город: {data['city']}")
    print(f"Раундов: {data['rounds']}")
    print(f"Даты: {data['start_date']} - {data['end_date']}")
    
    return data


def parse_round(html_file: str, output: str = None):
    """Парсинг страницы с результатами тура."""
    parser = ChessResultsRoundParser(SessionManager(CacheManager()))
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    data = parser.parse(html)
    
    if output:
        import json
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Тур: {data['round']}")
    print(f"Партий: {len(data['games'])}")
    
    for game in data['games'][:5]:  # Показать первые 5 партий
        print(f"  Доска {game['board']}: {game['white_name']} ({game['white_rating']}) "
              f"- {game['black_name']} ({game['black_rating']}) = {game['result']}")
    
    return data


def parse_player(html_file: str, output: str = None):
    """Парсинг страницы профиля игрока на chess-results.com."""
    parser = ChessResultsPlayerParser(SessionManager(CacheManager()))
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    data = parser.parse(html)
    
    if output:
        import json
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Имя: {data['name']}")
    print(f"ID: {data['rus_id']}")
    print(f"Рейтинг: {data['rating']}")
    print(f"Очки: {data['points']}")
    print(f"Место: {data['position']}")
    print(f"Игр: {len(data['games'])}")
    
    return data


def parse_ruchess_player(html_file: str, output: str = None):
    """Парсинг страницы профиля игрока на ruchess.ru."""
    parser = RuChessPlayerParser(SessionManager(CacheManager()))
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    data = parser.parse(html)
    
    if output:
        import json
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Имя: {data['name']}")
    print(f"ID: {data['rus_id']}")
    print(f"Пол: {data['gender']}")
    print(f"Регион: {data['region_name']}")
    print(f"Год рождения: {data['birth_year']}")
    print(f"\nТекущий рейтинг:")
    for rating_type, rating_data in data['current_ratings'].items():
        print(f"  {rating_type}: {rating_data['rating']} (место: {rating_data['rank']} из {rating_data['total']})")
    print(f"\nЗаписей в истории рейтинга: {len(data['rating_history'])}")
    print(f"Последних турниров: {len(data['last_tournaments'])}")
    
    return data


def main():
    parser = argparse.ArgumentParser(description='Парсер шахматных данных')
    parser.add_argument('--type', '-t', required=True, 
                        choices=['tournament', 'round', 'player', 'ruchess'],
                        help='Тип страницы для парсинга')
    parser.add_argument('--input', '-i', required=True,
                        help='Путь к HTML файлу')
    parser.add_argument('--output', '-o',
                        help='Путь к выходному JSON файлу')
    
    args = parser.parse_args()
    
    if args.type == 'tournament':
        parse_tournament(args.input, args.output)
    elif args.type == 'round':
        parse_round(args.input, args.output)
    elif args.type == 'player':
        parse_player(args.input, args.output)
    elif args.type == 'ruchess':
        parse_ruchess_player(args.input, args.output)


if __name__ == '__main__':
    main()