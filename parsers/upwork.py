from typing import List, Dict, Optional, Any, Union
import random
import time
import json
import re
import asyncio
import aiohttp
import ssl
from urllib.parse import urlencode, urljoin, parse_qs, urlparse
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from aiohttp_socks import ProxyConnector
from utils.keywords import KEYWORDS, EXCLUDE_WORDS
from .base_parser import BaseParser

# Инициализируем UserAgent
ua = UserAgent()

# Настройки для обхода защиты
REQUEST_DELAY = 5  # Задержка между запросами в секундах
MAX_RETRIES = 3     # Максимальное количество попыток повтора запроса

# Список прокси (если нужны)
PROXIES = [
    # 'socks5://user:pass@host:port',
    # 'http://user:pass@host:port',
]

def get_random_headers() -> Dict[str, str]:
    """Возвращает случайный набор заголовков для запроса"""
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'TE': 'trailers',
        'DNT': '1',
        'Sec-GPC': '1',
    }


class UpworkParser(BaseParser):
    """Парсер вакансий Upwork с обходом защиты."""

    def __init__(self, proxy: Optional[str] = None) -> None:
        super().__init__("Upwork", "https://www.upwork.com")
        self.search_url = f"{self.base_url}/nxsites/messages/threads/api/threads"
        self.proxy = proxy or (PROXIES[0] if PROXIES else None)
        self.connector = None
        self.cookies = {}
        self.session = None
        self.initialized = False

    async def _init_session(self) -> bool:
        """Инициализирует сессию с нужными куками и заголовками"""
        if self.initialized and self.session and not self.session.closed:
            return True
            
        try:
            # Настраиваем прокси, если есть
            if self.proxy:
                if self.proxy.startswith('socks'):
                    self.connector = ProxyConnector.from_url(self.proxy, ssl=False)
                else:
                    self.connector = aiohttp.TCPConnector(ssl=False)
                
            # Создаем сессию
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                headers=get_random_headers(),
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                trust_env=True
            )
            
            # Делаем начальный запрос для получения куков
            async with self.session.get(
                self.base_url,
                allow_redirects=True,
                ssl=ssl.SSLContext()
            ) as response:
                if response.status != 200:
                    self.logger.error(f"Failed to initialize session: {response.status}")
                    return False
                
                # Сохраняем куки
                self.cookies = {c.key: c.value for c in self.session.cookie_jar}
                
                # Получаем CSRF токен из HTML
                html = await response.text()
                self._save_debug_html(html, "init")
                
                # Парсим CSRF токен
                csrf_match = re.search(r'"csrfToken":"([^"]+)"', html)
                if csrf_match:
                    self.cookies['XSRF-TOKEN'] = csrf_match.group(1)
                    self.session.headers.update({
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-Odesk-Csrf-Token': self.cookies['XSRF-TOKEN']
                    })
                
                self.initialized = True
                return True
                
        except Exception as e:
            self.logger.error(f"Error initializing session: {e}", exc_info=True)
            if self.session:
                await self.session.close()
            self.initialized = False
            return False

    def _parse_project(self, item: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Парсит данные проекта из JSON-ответа"""
        try:
            title = item.get('title', '')
            description = item.get('description', '')
            url = item.get('ciphertext')
            
            if not all([title, description, url]):
                return None
                
            # Формируем полную ссылку
            full_url = urljoin(self.base_url, f'/job/{url}')
            
            # Собираем полный текст для проверки ключевых слов
            full_text = f"{title} {description}".lower()
            
            # Проверяем ключевые слова
            if (any(keyword in full_text for keyword in KEYWORDS) and 
                not any(exclude in full_text for exclude in EXCLUDE_WORDS)):
                
                return {
                    'title': title,
                    'link': full_url,
                    'description': description,
                    'price': item.get('amount', {}).get('amount', 'Договорная'),
                    'source': 'Upwork'
                }
                
        except Exception as e:
            self.logger.error(f"Error parsing project: {e}")
            
        return None

    async def _make_upwork_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Выполняет запрос к API Upwork с повторными попытками"""
        if not await self._init_session():
            return None
            
        for attempt in range(MAX_RETRIES):
            try:
                # Добавляем случайную задержку между запросами
                if attempt > 0:
                    await asyncio.sleep(REQUEST_DELAY * (attempt + 1))
                
                # Обновляем заголовки для каждого запроса
                headers = get_random_headers()
                if 'X-Odesk-Csrf-Token' in self.session.headers:
                    headers['X-Odesk-Csrf-Token'] = self.session.headers['X-Odesk-Csrf-Token']
                
                async with self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    ssl=ssl.SSLContext()
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status in [403, 429]:
                        self.logger.warning(f"Rate limited or blocked. Waiting before retry... (Attempt {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(10 * (attempt + 1))  # Увеличиваем задержку при блокировке
                    else:
                        self.logger.error(f"Request failed with status {response.status}")
                        break
                        
            except Exception as e:
                self.logger.error(f"Request error: {e}")
                if attempt == MAX_RETRIES - 1:
                    return None
                
        return None

    async def async_find_projects(self) -> List[Dict]:
        """Асинхронный поиск проектов на Upwork"""
        self.logger.info("🔍 Ищу заказы на Upwork...")
        projects = []
        
        try:
            # Параметры запроса
            params = {
                'page': '1',
                't': str(int(time.time() * 1000)),
                'filter': json.dumps({
                    'job_type': ['hourly', 'fixed'],
                    'job_status': ['open'],
                    'sort': 'create_time desc',
                    'q': ' OR '.join(KEYWORDS),
                    'limit': 50,
                    'offset': 0
                })
            }
            
            # Выполняем запрос
            data = await self._make_upwork_request(self.search_url, params)
            if not data or 'threads' not in data:
                self.logger.error("Invalid response format or no projects found")
                return []
            
            # Парсим проекты
            for item in data['threads']:
                project = self._parse_project(item)
                if project:
                    projects.append(project)
            
            self._log_projects(projects)
            
        except Exception as e:
            self.logger.error(f"Error in Upwork parser: {e}", exc_info=True)
            
        return projects
        
    def find_projects(self) -> List[Dict]:
        """Синхронная версия для обратной совместимости"""
        import asyncio
        return asyncio.run(self.async_find_projects())
        try:
            self.logger.info("🔍 Ищу заказы на Upwork...")
            proxies = {'http': self.proxy, 'https': self.proxy} if self.proxy else None
            
            # Пробуем с разными User-Agents
            for attempt in range(3):
                try:
                    headers = get_random_headers()
                    self.logger.debug(f"Попытка {attempt + 1} с User-Agent: {headers['User-Agent'][:50]}...")
                    
                    response = requests.get(
                        self.search_url,
                        headers=headers,
                        proxies=proxies,
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    if 'captcha' in response.text.lower() or 'access denied' in response.text.lower():
                        self.logger.warning("Обнаружена капча или доступ запрещен. Пробуем другой User-Agent...")
                        continue
                        
                    projects = self._parse_html(response.text)
                    filtered = self._filter_projects(projects, KEYWORDS, EXCLUDE_WORDS)
                    self._log_projects(filtered)
                    return filtered
                    
                except requests.RequestException as e:
                    self.logger.warning(f"Попытка {attempt + 1} не удалась: {e}")
                    if attempt == 2:  # Если это была последняя попытка
                        raise
                    
            return []
            
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге Upwork: {e}", exc_info=True)
            return []

    async def async_find_projects(self) -> List[Dict]:
        """Асинхронный поиск проектов на Upwork."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Настройка прокси для aiohttp
        conn = None
        if self.proxy:
            from aiohttp_socks import ProxyConnector
            connector = ProxyConnector.from_url(self.proxy, ssl=ssl_context)
        else:
            connector = aiohttp.TCPConnector(ssl=ssl_context)

        try:
            for attempt in range(3):
                try:
                    headers = get_random_headers()
                    self.logger.debug(f"Попытка {attempt + 1} с User-Agent: {headers['User-Agent'][:50]}...")
                    
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get(
                            self.search_url,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            text = await response.text()
                            
                            if response.status != 200:
                                self.logger.warning(f"Ошибка {response.status} при запросе к Upwork")
                                continue
                                
                            if 'captcha' in text.lower() or 'access denied' in text.lower():
                                self.logger.warning("Обнаружена капча или доступ запрещен. Пробуем другой User-Agent...")
                                continue
                                
                            projects = self._parse_html(text)
                            filtered = self._filter_projects(projects, KEYWORDS, EXCLUDE_WORDS)
                            self._log_projects(filtered)
                            return filtered
                            
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    self.logger.warning(f"Попытка {attempt + 1} не удалась: {e}")
                    if attempt == 2:  # Если это была последняя попытка
                        raise
                    await asyncio.sleep(1)  # Небольшая задержка между попытками
                    
            return []
            
        except Exception as e:
            self.logger.error(f"Ошибка при асинхронном парсинге Upwork: {e}", exc_info=True)
            return []
            
        finally:
            if conn:
                await conn.close()

    def _parse_html(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        projects: List[Dict] = []
        for item in soup.select("section.up-card-section"):
            try:
                title_tag = item.select_one("a.job-title-link") or item.select_one("a")
                desc_tag = item.select_one("p")
                price_tag = item.select_one(".amount")
                if title_tag and desc_tag:
                    href = title_tag["href"]
                    projects.append({
                        "title": title_tag.text.strip(),
                        "link": self.base_url + href,
                        "description": desc_tag.text.strip(),
                        "price": price_tag.text.strip() if price_tag else "Цена не указана",
                    })
            except Exception as e:  # pragma: no cover - logging only
                self.logger.error(f"Ошибка обработки проекта: {e}")
        return projects
