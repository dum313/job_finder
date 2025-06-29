import os
import logging
import time
import aiohttp
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Create debug directory if it doesn't exist
DEBUG_DIR = Path("debug_parser")
DEBUG_DIR.mkdir(exist_ok=True)

class BaseParser(ABC):
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.logger = logging.getLogger(f"parser.{name}")
        self.debug_mode = os.getenv("DEBUG_PARSER") == "1"

    @abstractmethod
    def find_projects(self) -> List[Dict]:
        """Находит проекты на платформе"""
        pass

    def _filter_projects(self, projects: List[Dict], keywords: List[str], exclude_words: List[str]) -> List[Dict]:
        """Фильтрует проекты по ключевым словам"""
        filtered = []
        for project in projects:
            text = f"{project.get('title', '')} {project.get('description', '')}".lower()
            
            # Проверяем наличие ключевых слов и отсутствие исключающих слов
            if (any(keyword in text for keyword in keywords) and
                not any(exclude in text for exclude in exclude_words)):
                filtered.append(project)
        
        return filtered

    def _save_debug_html(self, html: str, prefix: str = "") -> None:
        """Сохраняет HTML для отладки"""
        if not self.debug_mode:
            return
            
        timestamp = int(time.time())
        filename = f"{self.name.lower().replace('.', '_')}_{prefix}_{timestamp}.html"
        filepath = DEBUG_DIR / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html[:100000])  # Save first 100KB to avoid huge files
            self.logger.debug(f"Сохранен отладочный HTML в {filepath}")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении отладочного HTML: {e}")

    async def _make_request(self, url: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]:
        """Выполняет HTTP-запрос с сохранением отладочной информации"""
        try:
            if session:
                async with session.get(url) as response:
                    text = await response.text()
                    if self.debug_mode:
                        self._save_debug_html(text, f"{response.status}")
                    return text
            else:
                response = requests.get(url, timeout=30)
                if self.debug_mode:
                    self._save_debug_html(response.text, str(response.status_code))
                return response.text
        except Exception as e:
            self.logger.error(f"Ошибка при запросе {url}: {e}")
            return None

    def _log_projects(self, projects: List[Dict]):
        """Логирует найденные проекты"""
        if projects:
            self.logger.info(f"Найдено {len(projects)} проектов на {self.name}")
        else:
            self.logger.info(f"Новых проектов на {self.name} не найдено")
