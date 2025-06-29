from typing import List, Dict, Optional
import urllib.parse
from bs4 import BeautifulSoup
from utils.keywords import KEYWORDS, EXCLUDE_WORDS
from .base_parser import BaseParser


class FLRuParser(BaseParser):
    def __init__(self):
        super().__init__("FL.ru", "https://www.fl.ru")
        self.search_url = f"{self.base_url}/projects/"

    async def _parse_project_card(self, card) -> Optional[Dict]:
        """Парсит карточку проекта"""
        try:
            # Пытаемся найти заголовок и ссылку
            title_elem = card.select_one('a.b-post__link')
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            relative_url = title_elem.get('href', '')
            
            # Парсим описание
            desc_elem = card.select_one('div.b-post__txt')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Парсим цену, если есть
            price_elem = card.select_one('div.b-post__price')
            price = price_elem.get_text(strip=True) if price_elem else 'Цена не указана'
            
            # Собираем полный текст для проверки ключевых слов
            full_text = f"{title} {description}".lower()
            
            # Проверяем ключевые слова
            if (any(keyword in full_text for keyword in KEYWORDS) and 
                not any(exclude in full_text for exclude in EXCLUDE_WORDS)):
                
                return {
                    'title': title,
                    'link': urllib.parse.urljoin(self.base_url, relative_url),
                    'description': description,
                    'price': price,
                    'source': 'FL.ru'
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге карточки проекта: {e}")
        
        return None

    async def async_find_projects(self) -> List[Dict]:
        """Асинхронно ищет проекты на FL.ru"""
        self.logger.info("🔍 Ищу заказы на FL.ru...")
        projects = []
        
        try:
            # Используем базовый метод для запроса с поддержкой отладки
            html = await self._make_request(self.search_url)
            if not html:
                return []
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем карточки проектов
            project_cards = soup.select('div.project-card')
            if not project_cards:
                # Пробуем альтернативный селектор
                project_cards = soup.select('div.b-post')
                
            self.logger.info(f"Найдено карточек проектов: {len(project_cards)}")
            
            # Парсим каждую карточку
            for card in project_cards:
                project = await self._parse_project_card(card)
                if project:
                    projects.append(project)
                    
            self._log_projects(projects)
            
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге FL.ru: {e}", exc_info=True)
            
        return projects
        
    def find_projects(self) -> List[Dict]:
        """Синхронная версия для обратной совместимости"""
        import asyncio
        return asyncio.run(self.async_find_projects())

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
