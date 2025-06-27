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
CRON_EXPRESSION = os.getenv('CRON_EXPRESSION')  # Cron, если указан
TIMEZONE = os.getenv('TIMEZONE', 'UTC')  # Часовой пояс планировщика
MAX_RETRIES = 3       # Максимальное количество попыток при ошибке
RETRY_DELAY = 5       # Задержка между попытками (секунды)

# Настройки логирования
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Создаем директорию для логов, если её нет
LOG_DIR = 'logs'
Path(LOG_DIR).mkdir(exist_ok=True)

# Основные настройки логирования
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3

# Настройки файлов логов
LOG_FILES = {
    'parser': {
        'filename': f'{LOG_DIR}/parser.log',
        'level': LOG_LEVEL,
        'maxBytes': LOG_MAX_BYTES,
        'backupCount': LOG_BACKUP_COUNT,
        'encoding': 'utf-8'
    },
    'bot': {
        'filename': f'{LOG_DIR}/bot.log',
        'level': LOG_LEVEL,
        'maxBytes': LOG_MAX_BYTES,
        'backupCount': LOG_BACKUP_COUNT,
        'encoding': 'utf-8'
    },
    'debug': {
        'filename': f'{LOG_DIR}/debug.log',
        'level': logging.DEBUG,
        'maxBytes': LOG_MAX_BYTES,
        'backupCount': LOG_BACKUP_COUNT,
        'encoding': 'utf-8'
    }
}

def setup_logger(name, log_config):
    """Настройка логгера с ротацией логов"""
    logger = logging.getLogger(name)
    logger.setLevel(log_config['level'])
    
    # Создаем обработчик с ротацией
    handler = RotatingFileHandler(
        filename=log_config['filename'],
        maxBytes=log_config['maxBytes'],
        backupCount=log_config['backupCount'],
        encoding=log_config['encoding']
    )
    
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    
    # Добавляем обработчик только если его еще нет
    if not any(isinstance(h, RotatingFileHandler) and h.baseFilename == handler.baseFilename 
              for h in logger.handlers):
        logger.addHandler(handler)
    
    # Добавляем вывод в консоль
    console = logging.StreamHandler()
    console.setLevel(log_config['level'])
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    return logger

# Настройки парсинга
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
