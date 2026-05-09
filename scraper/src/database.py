"""
Интеграция с PostgreSQL базой данных Chessfan.
"""

import logging
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с PostgreSQL базой данных."""
    
    def __init__(self, host: str = "localhost", port: int = 5432,
                 database: str = "chessfan", user: str = "chessfan",
                 password: str = "chessfan123"):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
    
    def connect(self) -> bool:
        """Подключение к базе данных."""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Connected to database {self.database}")
            return True
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def close(self) -> None:
        """Закрытие соединения с базой данных."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
            self.conn = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[list]:
        """Выполнение SELECT запроса."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except psycopg2.Error as e:
            logger.error(f"Query execution failed: {e}")
            return None
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Выполнение INSERT/UPDATE/DELETE запроса. Возвращает количество затронутых строк."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()
                return cursor.rowcount
        except psycopg2.Error as e:
            logger.error(f"Update execution failed: {e}")
            self.conn.rollback()
            return 0
    
    # --- Методы для работы с игроками ---
    
    def get_player_by_rus_id(self, rus_id: int) -> Optional[Dict[str, Any]]:
        """Получить игрока по rus_id."""
        query = """
            SELECT id, rus_id, name, gender, birth_year, city, created_at
            FROM players WHERE rus_id = %s
        """
        result = self.execute_query(query, (rus_id,))
        return result[0] if result else None
    
    def get_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Получить игрока по id."""
        query = """
            SELECT id, rus_id, name, gender, birth_year, city, created_at
            FROM players WHERE id = %s
        """
        result = self.execute_query(query, (player_id,))
        return result[0] if result else None
    
    def upsert_player(self, player_data: Dict[str, Any]) -> int:
        """
        Вставить или обновить игрока.
        Возвращает id игрока.
        """
        query = """
            INSERT INTO players (rus_id, name, gender, birth_year, city)
            VALUES (%(rus_id)s, %(name)s, %(gender)s, %(birth_year)s, %(city)s)
            ON CONFLICT (rus_id) DO UPDATE SET
                name = EXCLUDED.name,
                gender = EXCLUDED.gender,
                birth_year = EXCLUDED.birth_year,
                city = EXCLUDED.city
            RETURNING id
        """
        result = self.execute_query(query, (player_data,))
        return result[0]['id'] if result else None
    
    # --- Методы для работы с турнирами ---
    
    def get_tournament_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Получить турнир по названию."""
        query = """
            SELECT id, name, location, start_date, end_date, created_at
            FROM tournaments WHERE name = %s
        """
        result = self.execute_query(query, (name,))
        return result[0] if result else None
    
    def get_tournament_by_id(self, tournament_id: int) -> Optional[Dict[str, Any]]:
        """Получить турнир по id."""
        query = """
            SELECT id, name, location, start_date, end_date, created_at
            FROM tournaments WHERE id = %s
        """
        result = self.execute_query(query, (tournament_id,))
        return result[0] if result else None
    
    def upsert_tournament(self, tournament_data: Dict[str, Any]) -> int:
        """
        Вставить или обновить турнир.
        Возвращает id турнира.
        """
        query = """
            INSERT INTO tournaments (name, location, start_date, end_date)
            VALUES (%(name)s, %(location)s, %(start_date)s, %(end_date)s)
            ON CONFLICT (name, start_date, end_date) DO UPDATE SET
                location = EXCLUDED.location
            RETURNING id
        """
        result = self.execute_query(query, (tournament_data,))
        return result[0]['id'] if result else None
    
    # --- Методы для работы с участниками турнира ---
    
    def get_tournament_player(self, tournament_id: int, player_id: int) -> Optional[Dict[str, Any]]:
        """Получить запись участника турнира."""
        query = """
            SELECT id, tournament_id, player_id, rating_at_tournament, title, seed
            FROM tournament_players 
            WHERE tournament_id = %s AND player_id = %s
        """
        result = self.execute_query(query, (tournament_id, player_id))
        return result[0] if result else None
    
    def upsert_tournament_player(self, tournament_id: int, player_id: int, 
                                  player_data: Dict[str, Any]) -> int:
        """
        Вставить или обновить участника турнира.
        Возвращает id записи.
        """
        query = """
            INSERT INTO tournament_players (tournament_id, player_id, rating_at_tournament, title, seed)
            VALUES (%s, %s, %(rating_at_tournament)s, %(title)s, %(seed)s)
            ON CONFLICT (tournament_id, player_id) DO UPDATE SET
                rating_at_tournament = EXCLUDED.rating_at_tournament,
                title = EXCLUDED.title,
                seed = EXCLUDED.seed
            RETURNING id
        """
        params = (tournament_id, player_id, player_data)
        result = self.execute_query(query, params)
        return result[0]['id'] if result else None
    
    # --- Методы для работы с играми ---
    
    def get_game(self, tournament_id: int, round_num: int, 
                  white_id: int, black_id: int) -> Optional[Dict[str, Any]]:
        """Получить игру по параметрам."""
        query = """
            SELECT id, tournament_id, round, white_player_id, black_player_id, score
            FROM games 
            WHERE tournament_id = %s AND round = %s 
              AND white_player_id = %s AND black_player_id = %s
        """
        result = self.execute_query(query, (tournament_id, round_num, white_id, black_id))
        return result[0] if result else None
    
    def upsert_game(self, game_data: Dict[str, Any]) -> int:
        """
        Вставить или обновить игру.
        Возвращает id игры.
        """
        query = """
            INSERT INTO games (tournament_id, round, white_player_id, black_player_id, score)
            VALUES (%(tournament_id)s, %(round)s, %(white_player_id)s, %(black_player_id)s, %(score)s)
            ON CONFLICT (tournament_id, round, white_player_id, black_player_id) DO UPDATE SET
                score = EXCLUDED.score
            RETURNING id
        """
        result = self.execute_query(query, (game_data,))
        return result[0]['id'] if result else None
    
    # --- Методы для работы с рейтингами ---
    
    def get_player_rating(self, player_id: int, rating_date: str) -> Optional[Dict[str, Any]]:
        """Получить рейтинг игрока на определенную дату."""
        query = """
            SELECT id, player_id, rating, rating_date, source_tournament_id
            FROM player_ratings 
            WHERE player_id = %s AND rating_date = %s
        """
        result = self.execute_query(query, (player_id, rating_date))
        return result[0] if result else None
    
    def upsert_player_rating(self, player_id: int, rating_data: Dict[str, Any]) -> int:
        """
        Вставить или обновить рейтинг игрока.
        Возвращает id записи.
        """
        query = """
            INSERT INTO player_ratings (player_id, rating, rating_date, source_tournament_id)
            VALUES (%s, %(rating)s, %(rating_date)s, %(source_tournament_id)s)
            ON CONFLICT (player_id, rating_date) DO UPDATE SET
                rating = EXCLUDED.rating,
                source_tournament_id = EXCLUDED.source_tournament_id
            RETURNING id
        """
        params = (player_id, rating_data)
        result = self.execute_query(query, params)
        return result[0]['id'] if result else None
    
    # --- Методы для работы с позициями в турнире ---
    
    def get_tournament_standings(self, tournament_id: int, player_id: int, 
                                  round_num: int) -> Optional[Dict[str, Any]]:
        """Получить позицию игрока в турнире."""
        query = """
            SELECT id, tournament_id, player_id, round_number, points, position
            FROM tournament_standings 
            WHERE tournament_id = %s AND player_id = %s AND round_number = %s
        """
        result = self.execute_query(query, (tournament_id, player_id, round_num))
        return result[0] if result else None
    
    def upsert_tournament_standings(self, tournament_id: int, player_id: int,
                                     standings_data: Dict[str, Any]) -> int:
        """
        Вставить или обновить позицию игрока в турнире.
        Возвращает id записи.
        """
        query = """
            INSERT INTO tournament_standings (tournament_id, player_id, round_number, points, position)
            VALUES (%s, %s, %(round_number)s, %(points)s, %(position)s)
            ON CONFLICT (tournament_id, player_id, round_number) DO UPDATE SET
                points = EXCLUDED.points,
                position = EXCLUDED.position
            RETURNING id
        """
        params = (tournament_id, player_id, standings_data)
        result = self.execute_query(query, params)
        return result[0]['id'] if result else None