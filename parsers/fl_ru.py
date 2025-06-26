from typing import List, Dict, Any, Optional
import ssl
import requests
import aiohttp
from bs4 import BeautifulSoup
from config import HEADERS
from utils.keywords import KEYWORDS, EXCLUDE_WORDS
from .base_parser import BaseParser


class FLRuParser(BaseParser):
    def __init__(self):
        super().__init__("FL.ru", "https://www.fl.ru")
        self.search_url = f"{self.base_url}/projects/"

    def find_projects(self) -> List[Dict]:
        """Ищет заказы на FL.ru"""
        try:
            self.logger.info("🔍 Ищу заказы на FL.ru...")
            response = requests.get(self.search_url, headers=HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            projects = []
            
            # Находим все проекты на странице
            project_items = soup.select('.b-post')
            
            for item in project_items:
                try:
                    title = item.select_one('.b-post__link')
                    desc = item.select_one('.b-post__txt')
                    price = item.select_one('.b-post__price')
                    
                    if title and desc:
                        project = {
                            'title': title.text.strip(),
                            'link': f"{self.base_url}{title['href']}",
                            'description': desc.text.strip(),
                            'price': price.text.strip() if price else "Цена не указана"
                        }
                        projects.append(project)
                except Exception as e:
                    self.logger.error(f"Ошибка при обработке проекта: {e}")
                    continue
            
            # Фильтруем проекты по ключевым словам
            filtered_projects = self._filter_projects(projects, KEYWORDS, EXCLUDE_WORDS)
            self._log_projects(filtered_projects)
            return filtered_projects
            
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при получении данных с FL.ru: {e}")
            return []

    async def async_find_projects(self) -> List[Dict]:
        """Асинхронная версия парсинга"""
        # Отключаем проверку SSL для тестового режима
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.search_url,
                    headers=HEADERS,
                    ssl=ssl_context,
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

    async def _async_parse_response(self, html):
        # Реализация аналогична синхронной версии
        soup = BeautifulSoup(html, 'html.parser')
        projects = []
        
        for project in soup.select('.b-post'):
            try:
                title = project.select_one('.b-post__link')
                desc = project.select_one('.b-post__txt')
                price = project.select_one('.b-post__price')
                
                if title and desc:
                    project = {
                        'title': title.text.strip(),
                        'link': f"{self.base_url}{title['href']}",
                        'description': desc.text.strip(),
                        'price': price.text.strip() if price else "Цена не указана"
                    }
                    projects.append(project)
            except Exception as e:
                self.logger.error(f"Ошибка обработки проекта: {e}")
        
        return projects

    async_parse = async_find_projects  # Алиас для совместимости
