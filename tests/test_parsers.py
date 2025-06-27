import unittest
import asyncio
from unittest.mock import patch
import aiohttp
from parsers.freelance_ru import FreelanceRuParser
from utils import storage


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

class TestFreelanceRuParser(unittest.TestCase):
    def setUp(self):
        storage.init(':memory:')
        self.parser = FreelanceRuParser()

    HTML_NO_KEYWORDS = (
        '<div class="content">\n'
        '  <div class="proj">\n'
        '    <div class="ptitle"><a href="/p2">Написать скрипт</a></div>\n'
        '    <div class="ptxt">Описание</div>\n'
        '  </div>\n'
        '</div>'
    )

    def test_parser_init(self):
        self.assertIsNotNone(self.parser)
        self.assertTrue(hasattr(self.parser, 'base_url'))
        self.assertTrue(hasattr(self.parser, 'search_url'))

    def test_async_parse(self):
        """Тестируем асинхронный парсинг"""
        async def test():
            HTML = (
                '<div class="content">\n'
                '  <div class="proj">\n'
                '    <div class="ptitle"><a href="/p1">Создать сайт</a></div>\n'
                '    <div class="ptxt">Описание</div>\n'
                '  </div>\n'
                '</div>'
            )
            try:
                with patch('aiohttp.ClientSession', return_value=_mock_session_factory(HTML)):
                    result = await self.parser.async_find_projects()
                    self.assertIsInstance(result, list)
                    self.assertEqual(len(result), 1)
                    self.assertEqual(result[0]['title'], 'Создать сайт')
            except aiohttp.ClientConnectorError as e:
                self.skipTest(f"Не удалось подключиться к серверу: {e}")
            except Exception as e:
                self.fail(f"Асинхронный парсинг завершился с ошибкой: {e}")
        
        asyncio.run(test())

    def test_async_parse_no_keywords(self):
        """Заказ без ключевых слов должен быть отфильтрован"""
        async def test():
            with patch('aiohttp.ClientSession', return_value=_mock_session_factory(self.HTML_NO_KEYWORDS)):
                result = await self.parser.async_find_projects()
                self.assertEqual(result, [])
        asyncio.run(test())
