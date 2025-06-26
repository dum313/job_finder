import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
env_path = Path('.') / '.env'
load_dotenv(env_path)

# Настройки Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("Telegram token не найден в .env файле")
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Настройки парсинга
PARSING_INTERVAL = 30  # Минуты между проверками
MAX_RETRIES = 3       # Максимальное количество попыток при ошибке
RETRY_DELAY = 5       # Задержка между попытками (секунды)

# Настройки логирования
LOG_FILE = 'parser.log'
LOG_LEVEL = 'INFO'

# Настройки парсинга
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
