import asyncio
import unittest
from unittest.mock import patch
import requests

from parsers.upwork import UpworkParser


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


class TestUpworkParser(unittest.TestCase):
    HTML = (
        '<section class="up-card-section">\n'
        '  <a class="job-title-link" href="/u1">Create website</a>\n'
        '  <p>Description</p>\n'
        '  <span class="amount">100</span>\n'
        '</section>'
    )

    HTML_NO_KEYWORDS = (
        '<section class="up-card-section">\n'
        '  <a class="job-title-link" href="/u2">Write script</a>\n'
        '  <p>Description</p>\n'
        '  <span class="amount">100</span>\n'
        '</section>'
    )

    def setUp(self):
        self.parser = UpworkParser()

    @patch('parsers.upwork.requests.get')
    def test_find_projects(self, mock_get):
        mock_get.return_value = _MockRequestsResponse(self.HTML)
        projects = self.parser.find_projects()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]['title'], 'Create website')

    @patch('parsers.upwork.requests.get')
    def test_find_projects_no_keywords(self, mock_get):
        mock_get.return_value = _MockRequestsResponse(self.HTML_NO_KEYWORDS)
        projects = self.parser.find_projects()
        self.assertEqual(projects, [])

    def test_async_find_projects(self):
        async def run():
            with patch('aiohttp.ClientSession', return_value=_mock_session_factory(self.HTML)):
                projects = await self.parser.async_find_projects()
                self.assertEqual(len(projects), 1)
                self.assertEqual(projects[0]['title'], 'Create website')
        asyncio.run(run())

    def test_async_find_projects_no_keywords(self):
        async def run():
            with patch('aiohttp.ClientSession', return_value=_mock_session_factory(self.HTML_NO_KEYWORDS)):
                projects = await self.parser.async_find_projects()
                self.assertEqual(projects, [])
        asyncio.run(run())
