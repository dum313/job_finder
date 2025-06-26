import unittest
import asyncio
import aiohttp
from parsers.freelance_ru import FreelanceRuParser

class TestFreelanceRuParser(unittest.TestCase):
    def setUp(self):
        self.parser = FreelanceRuParser()

    def test_parser_init(self):
        self.assertIsNotNone(self.parser)
        self.assertTrue(hasattr(self.parser, 'base_url'))
        self.assertTrue(hasattr(self.parser, 'search_url'))

    def test_async_parse(self):
        """Тестируем асинхронный парсинг"""
        async def test():
            try:
                result = await self.parser.async_find_projects()
                self.assertIsInstance(result, list)
                # Проверяем, что результат - это список словарей с ожидаемыми ключами
                if result:  # если список не пустой
                    self.assertIn('title', result[0])
                    self.assertIn('url', result[0])
            except aiohttp.ClientConnectorError as e:
                self.skipTest(f"Не удалось подключиться к серверу: {e}")
            except Exception as e:
                self.fail(f"Асинхронный парсинг завершился с ошибкой: {e}")
        
        asyncio.run(test())
