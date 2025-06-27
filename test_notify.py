import asyncio
import logging
import os
import pytest
from utils.notifier import notify_user
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

pytest.skip(
    "Manual test requiring real Telegram credentials and network access",
    allow_module_level=True,
)

# Выводим отладочную информацию
print("Проверка переменных окружения:")
print(f"TELEGRAM_TOKEN: {'установлен' if TELEGRAM_TOKEN else 'не установлен'}")
print(f"TELEGRAM_CHAT_ID: {'установлен' if TELEGRAM_CHAT_ID else 'не установлен'}")
if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("ОШИБКА: Необходимо установить TELEGRAM_TOKEN и TELEGRAM_CHAT_ID в файле .env")
    exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_notify.log')
    ]
)

async def test_notification():
    import time
    test_project = {
        'title': 'Тестовое уведомление',
        'description': 'Это тестовое сообщение от бота',
        'link': f'https://example.com/test_{int(time.time())}',  # Уникальная ссылка для каждого теста
        'price': '1000',
        'platform': 'Test'
    }
    print("Отправляю тестовое уведомление...")
    await notify_user(test_project)
    print("Проверьте, пришло ли сообщение в Telegram")

if __name__ == "__main__":
    asyncio.run(test_notification())
