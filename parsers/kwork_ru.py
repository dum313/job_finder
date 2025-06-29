from typing import List, Dict, Optional
import urllib.parse
from bs4 import BeautifulSoup
from utils.keywords import KEYWORDS, EXCLUDE_WORDS
from .base_parser import BaseParser


class KworkRuParser(BaseParser):
    def __init__(self):
        super().__init__("Kwork.ru", "https://kwork.ru")
        self.search_url = f"{self.base_url}/orders"

    async def _parse_project_card(self, card) -> Optional[Dict]:
        """Парсит карточку проекта"""
        try:
            # Пытаемся найти заголовок и ссылку
            title_elem = card.select_one('a[data-test-id="order-card-title"]')
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            relative_url = title_elem.get('href', '')
            
            # Парсим описание
            desc_elem = card.select_one('div[data-test-id="order-card-description"]')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Парсим цену, если есть
            price_elem = card.select_one('div[data-test-id="order-card-price"]')
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
                    'source': 'Kwork.ru'
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге карточки проекта: {e}")
        
        return None

    async def async_find_projects(self) -> List[Dict]:
        """Асинхронно ищет проекты на Kwork.ru"""
        self.logger.info("🔍 Ищу заказы на Kwork.ru...")
        projects = []
        
        try:
            # Используем базовый метод для запроса с поддержкой отладки
            html = await self._make_request(self.search_url)
            if not html:
                return []
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем карточки проектов
            project_cards = soup.select('div.card.card--order')
            if not project_cards:
                # Пробуем альтернативный селектор
                project_cards = soup.select('div[data-test-id="order-card"]')
                
            self.logger.info(f"Найдено карточек проектов: {len(project_cards)}")
            
            # Парсим каждую карточку
            for card in project_cards:
                project = await self._parse_project_card(card)
                if project:
                    projects.append(project)
                    
            self._log_projects(projects)
            
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге Kwork.ru: {e}", exc_info=True)
            
        return projects
        
    def find_projects(self) -> List[Dict]:
        """Синхронная версия для обратной совместимости"""
        import asyncio
        return asyncio.run(self.async_find_projects())

    async def async_find_projects(self) -> List[Dict]:
        """Асинхронно ищет проекты на kwork.ru"""
        url = self.search_url
        projects = []
        
        # Отключаем проверку SSL для тестового режима
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=HEADERS, ssl=ssl_context) as response:
                    if response.status == 200:
                        projects = await self._async_parse_response(await response.text())
                        filtered = self._filter_projects(projects, KEYWORDS, EXCLUDE_WORDS)
                        self._log_projects(filtered)
                        return filtered
                    else:
                        self.logger.error(f"Ошибка при получении данных: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Ошибка парсера: {e}")
            raise

    async def _async_parse_response(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        projects = []

        for card in soup.select('.card'):
            try:
                title = card.select_one('.card__title a')
                desc = card.select_one('.card__description')
                price = card.select_one('.card__price')

                if title:
                    projects.append({
                        'title': title.text.strip(),
                        'link': self.base_url + title['href'],
                        'description': desc.text.strip() if desc else '',
                        'price': price.text.strip() if price else "Цена не указана"
                    })
            except Exception as e:
                self.logger.error(f"Ошибка обработки проекта: {e}")

        return projects
