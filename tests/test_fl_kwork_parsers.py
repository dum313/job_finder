import asyncio
import unittest
from unittest.mock import patch
import requests

from parsers.fl_ru import FLRuParser
from parsers.kwork_ru import KworkRuParser


class _MockRequestsResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
    def raise_for_status(self) -> None:
        if self.status_code != 200:
            raise requests.HTTPError(f"status {self.status_code}")


class _MockAiohttpResponse:
    def __init__(self, text: str, status: int = 200):
        self._text = text
        self.status = status
    async def text(self) -> str:
        return self._text
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass

def _mock_session_factory(html: str):
    class _Session:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        def get(self, *args, **kwargs):
            return _MockAiohttpResponse(html)
    return _Session()


class TestFLRuParser(unittest.TestCase):
    HTML = (
        '<div class="b-post">\n'
        '  <a class="b-post__link" href="/p1">Создать сайт</a>\n'
        '  <div class="b-post__txt">Описание</div>\n'
        '  <span class="b-post__price">1000</span>\n'
        '</div>'
    )

    HTML_NO_KEYWORDS = (
        '<div class="b-post">\n'
        '  <a class="b-post__link" href="/p2">Написать скрипт</a>\n'
        '  <div class="b-post__txt">Описание</div>\n'
        '  <span class="b-post__price">1000</span>\n'
        '</div>'
    )

    def setUp(self):
        self.parser = FLRuParser()

    @patch('parsers.fl_ru.requests.get')
    def test_find_projects(self, mock_get):
        mock_get.return_value = _MockRequestsResponse(self.HTML)
        projects = self.parser.find_projects()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]['title'], 'Создать сайт')

    @patch('parsers.fl_ru.requests.get')
    def test_find_projects_no_keywords(self, mock_get):
        mock_get.return_value = _MockRequestsResponse(self.HTML_NO_KEYWORDS)
        projects = self.parser.find_projects()
        self.assertEqual(projects, [])

    def test_async_find_projects(self):
        async def run():
            with patch('aiohttp.ClientSession', return_value=_mock_session_factory(self.HTML)):
                projects = await self.parser.async_find_projects()
                self.assertEqual(len(projects), 1)
                self.assertEqual(projects[0]['title'], 'Создать сайт')
        asyncio.run(run())

    def test_async_find_projects_no_keywords(self):
        async def run():
            with patch('aiohttp.ClientSession', return_value=_mock_session_factory(self.HTML_NO_KEYWORDS)):
                projects = await self.parser.async_find_projects()
                self.assertEqual(projects, [])
        asyncio.run(run())


class TestKworkRuParser(unittest.TestCase):
    HTML = (
        '<div class="card card--order">\n'
        '  <div class="card__title" href="/k1"><a href="/k1">Верстка сайта</a></div>\n'
        '  <div class="card__description">Описание</div>\n'
        '  <span class="card__price">1000 Р</span>\n'
        '</div>'
    )

    HTML_NO_KEYWORDS = (
        '<div class="card card--order">\n'
        '  <div class="card__title" href="/k2"><a href="/k2">Написать скрипт</a></div>\n'
        '  <div class="card__description">Описание</div>\n'
        '  <span class="card__price">1000 Р</span>\n'
        '</div>'
    )

    def setUp(self):
        self.parser = KworkRuParser()

    @patch('parsers.kwork_ru.requests.get')
    def test_find_projects(self, mock_get):
        mock_get.return_value = _MockRequestsResponse(self.HTML)
        projects = self.parser.find_projects()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]['title'], 'Верстка сайта')

    @patch('parsers.kwork_ru.requests.get')
    def test_find_projects_no_keywords(self, mock_get):
        mock_get.return_value = _MockRequestsResponse(self.HTML_NO_KEYWORDS)
        projects = self.parser.find_projects()
        self.assertEqual(projects, [])

    def test_async_find_projects(self):
        async def run():
            with patch('aiohttp.ClientSession', return_value=_mock_session_factory(self.HTML)):
                projects = await self.parser.async_find_projects()
                self.assertEqual(len(projects), 1)
                self.assertEqual(projects[0]['title'], 'Верстка сайта')
        asyncio.run(run())

    def test_async_find_projects_no_keywords(self):
        async def run():
            with patch('aiohttp.ClientSession', return_value=_mock_session_factory(self.HTML_NO_KEYWORDS)):
                projects = await self.parser.async_find_projects()
                self.assertEqual(projects, [])
        asyncio.run(run())
