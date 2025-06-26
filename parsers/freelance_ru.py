from typing import List, Dict, Any, Optional
import requests
import aiohttp
import ssl
import certifi
from .base_parser import BaseParser
from bs4 import BeautifulSoup
from config import HEADERS
from utils.keywords import KEYWORDS, EXCLUDE_WORDS
import logging

# Создаем пользовательский контекст SSL, который игнорирует ошибки проверки сертификата
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

logger = logging.getLogger(__name__)

class FreelanceRuParser(BaseParser):
    def __init__(self):
        super().__init__('Freelance.ru', 'https://freelance.ru')
        self.search_url = f'{self.base_url}/projects/'

    def find_projects(self):
        """Ищет заказы на freelance.ru"""
        try:
            self.logger.info("🔍 Ищу заказы на freelance.ru...")
            response = requests.get(self.search_url, headers=HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            projects = []
            
            # Находим все проекты на странице
            project_items = soup.select('.content .proj')
            
            for item in project_items:
                try:
                    title = item.select_one('.ptitle a')
                    desc = item.select_one('.ptxt')
                    
                    if title and desc:
                        # Получаем полный текст для поиска ключевых слов
                        full_text = (title.text + ' ' + desc.text).lower()
                        
                        # Проверяем наличие ключевых слов и отсутствие исключающих слов
                        if (any(keyword in full_text for keyword in KEYWORDS) and
                            not any(exclude in full_text for exclude in EXCLUDE_WORDS)):
                            
                            link = f'{self.base_url}{title["href"]}'
                            projects.append({
                                'title': title.text.strip(),
                                'link': link,
                                'description': desc.text.strip()
                            })
                except Exception as e:
                    self.logger.error(f"Ошибка при обработке проекта: {e}")
                    continue
            
            self.logger.info(f"Найдено {len(projects)} проектов на freelance.ru")
            return projects
            
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при получении данных с freelance.ru: {e}")
            return []

    async def async_find_projects(self) -> List[Dict]:
        """Асинхронная версия парсинга"""
        # Отключаем проверку SSL для тестового режима
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            conn = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=conn) as session:
                async with session.get(
                    self.search_url,
                    headers=HEADERS,
                    ssl=ssl_context if __name__ != '__main__' else None
                ) as response:
                    if response.status == 200:
                        projects = await self._async_parse_response(await response.text())
                        filtered = self._filter_projects(projects, KEYWORDS, EXCLUDE_WORDS)
                        self._log_projects(filtered)
                        return filtered
                    else:
                        self.logger.error(f"HTTP ошибка: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Ошибка парсера: {e}")
            raise

    async def _async_parse_response(self, response_text):
        soup = BeautifulSoup(response_text, 'html.parser')
        projects = []
        
        # Находим все проекты на странице
        project_items = soup.select('.content .proj')
        
        for item in project_items:
            try:
                title = item.select_one('.ptitle a')
                desc = item.select_one('.ptxt')
                
                if title and desc:
                    link = f'{self.base_url}{title["href"]}'
                    projects.append({
                        'title': title.text.strip(),
                        'link': link,
                        'description': desc.text.strip(),
                    })
            except Exception as e:
                self.logger.error(f"Ошибка при обработке проекта: {e}")
                continue

        return projects

    async_parse = async_find_projects  # Алиас для совместимости с main.py
