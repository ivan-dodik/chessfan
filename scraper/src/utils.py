"""
Утилиты для парсера: сессия, кэш, логирование.
"""

import os
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import requests
from requests.adapters import HTTPAdapter, Retry

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CacheManager:
    """Управление кэшем HTML-файлов."""
    
    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, url: str) -> str:
        """Генерация ключа кэша из URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get(self, url: str) -> Optional[str]:
        """Получить закэшированный HTML по URL."""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.html"
        
        if cache_file.exists():
            logger.info(f"Cache hit for {url}")
            return cache_file.read_text(encoding='utf-8')
        
        return None
    
    def set(self, url: str, html: str) -> None:
        """Сохранить HTML в кэш."""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.html"
        cache_file.write_text(html, encoding='utf-8')
        logger.info(f"Cache saved for {url}")
    
    def clear(self) -> None:
        """Очистить весь кэш."""
        for cache_file in self.cache_dir.glob("*.html"):
            cache_file.unlink()
        logger.info("Cache cleared")


class SessionManager:
    """Управление HTTP-сессией с retry-логикой."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.session = requests.Session()
        
        # Настройка retry-стратегии
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # User-Agent для имитации браузера
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def fetch(self, url: str, use_cache: bool = True) -> str:
        """Получить HTML с кэшированием и retry-логикой."""
        # Проверка кэша
        if use_cache:
            cached = self.cache_manager.get(url)
            if cached:
                return cached
        
        # Запрос к серверу
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            
            # Сохранение в кэш
            self.cache_manager.set(url, html)
            
            return html
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise


class BaseParser:
    """Базовый класс для всех парсеров."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.data = {}
    
    def fetch(self, url: str, use_cache: bool = True) -> str:
        """Получить HTML страницы."""
        return self.session_manager.fetch(url, use_cache)
    
    def parse(self, html: str) -> dict:
        """Парсинг HTML и извлечение данных."""
        raise NotImplementedError("Subclasses must implement parse method")
    
    def parse_url(self, url: str, use_cache: bool = True) -> dict:
        """Получить и распарсить страницу."""
        html = self.fetch(url, use_cache)
        return self.parse(html)