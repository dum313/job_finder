from typing import List, Dict, Optional
import aiohttp
import ssl
import urllib.parse
from .base_parser import BaseParser
from bs4 import BeautifulSoup
from utils.keywords import KEYWORDS, EXCLUDE_WORDS

class FreelanceRuParser(BaseParser):
    def __init__(self):
        super().__init__('Freelance.ru', 'https://freelance.ru')
        self.search_url = f'{self.base_url}/project/search/'

    async def _parse_project_card(self, card) -> Optional[Dict]:
        """Парсит карточку проекта"""
        try:
            # Пытаемся найти заголовок и ссылку
            title_elem = card.select_one('h2 a')
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            relative_url = title_elem.get('href', '')
            
            # Парсим описание
            desc_elem = card.select_one('div[class*="description"]')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Парсим цену, если есть
            price_elem = card.select_one('div[class*="price"]')
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
                    'source': 'Freelance.ru'
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге карточки проекта: {e}")
        
        return None

    async def async_find_projects(self) -> List[Dict]:
        """Асинхронно ищет проекты на Freelance.ru"""
        self.logger.info("🔍 Ищу заказы на Freelance.ru...")
        projects = []
        
        try:
            # Используем базовый метод для запроса с поддержкой отладки
            html = await self._make_request(self.search_url)
            if not html:
                return []
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем карточки проектов
            project_cards = soup.select('article.project-card')
            if not project_cards:
                # Пробуем альтернативный селектор
                project_cards = soup.select('div.project')
                
            self.logger.info(f"Найдено карточек проектов: {len(project_cards)}")
            
            # Парсим каждую карточку
            for card in project_cards:
                project = await self._parse_project_card(card)
                if project:
                    projects.append(project)
                    
            self._log_projects(projects)
            
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге Freelance.ru: {e}", exc_info=True)
            
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
        project_items = soup.select('div.proj')
        
        for item in project_items:
            try:
                title_elem = item.select_one('.ptitle a')
                desc_elem = item.select_one('.ptxt')
                
                if title_elem and desc_elem:
                    title = title_elem.text.strip()
                    desc = desc_elem.text.strip()
                    full_text = f"{title} {desc}".lower()
                    
                    if (any(keyword in full_text for keyword in KEYWORDS) and
                        not any(exclude in full_text for exclude in EXCLUDE_WORDS)):
                        
                        link = f"{self.base_url}{title_elem['href']}"
                        projects.append({
                            'title': title,
                            'link': link,
                            'description': desc
                        })
            except Exception as e:
                self.logger.error(f"Ошибка при обработке проекта: {e}")
                continue

        return projects
