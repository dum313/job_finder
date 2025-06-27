from typing import List, Dict
import ssl
import requests
import aiohttp
from bs4 import BeautifulSoup
from config import HEADERS
from utils.keywords import KEYWORDS, EXCLUDE_WORDS
from .base_parser import BaseParser


class UpworkParser(BaseParser):
    """Парсер вакансий Upwork."""

    def __init__(self) -> None:
        super().__init__("Upwork", "https://www.upwork.com")
        self.search_url = f"{self.base_url}/ab/feed/jobs"

    def find_projects(self) -> List[Dict]:
        """Синхронный поиск проектов на Upwork."""
        try:
            self.logger.info("🔍 Ищу заказы на Upwork...")
            response = requests.get(self.search_url, headers=HEADERS)
            response.raise_for_status()
            projects = self._parse_html(response.text)
            filtered = self._filter_projects(projects, KEYWORDS, EXCLUDE_WORDS)
            self._log_projects(filtered)
            return filtered
        except requests.RequestException as e:
            self.logger.error(f"Ошибка при получении данных с Upwork: {e}")
            return []

    async def async_find_projects(self) -> List[Dict]:
        """Асинхронный поиск проектов на Upwork."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.search_url, headers=HEADERS, ssl=ssl_context) as response:
                    if response.status == 200:
                        text = await response.text()
                        projects = self._parse_html(text)
                        filtered = self._filter_projects(projects, KEYWORDS, EXCLUDE_WORDS)
                        self._log_projects(filtered)
                        return filtered
                    else:
                        self.logger.error(f"Ошибка при получении данных: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Ошибка парсера: {e}")
            raise

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
