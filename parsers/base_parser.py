import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseParser(ABC):
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.logger = logging.getLogger(f"parser.{name}")

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

    def _log_projects(self, projects: List[Dict]):
        """Логирует найденные проекты"""
        if projects:
            self.logger.info(f"Найдено {len(projects)} проектов на {self.name}")
        else:
            self.logger.info(f"Новых проектов на {self.name} не найдено")
