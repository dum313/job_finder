import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from parsers.freelance_ru import FreelanceRuParser
from parsers.fl_ru import FLRuParser
from parsers.kwork_ru import KworkRuParser
from parsers.upwork import UpworkParser
from utils.notifier import notify_user
from utils.telegram_bot import create_application
from config import (
    PARSING_INTERVAL,
    CRON_EXPRESSION,
    TIMEZONE,
    LOG_FILE,
    LOG_LEVEL,
)
from logging.handlers import RotatingFileHandler

# Настройка логирования
handler = RotatingFileHandler(
    filename=LOG_FILE,
    maxBytes=1024*1024,  # 1MB
    backupCount=3,
    encoding='utf-8'
)
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler, logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def job():
    """Основная функция, которая выполняется по расписанию"""
    logger.info("🔍 Начинаю поиск заказов...")
    
    try:
        # Создаем список парсеров
        parsers = [
            FreelanceRuParser(),
            FLRuParser(),
            KworkRuParser(),
            UpworkParser(),
        ]
        
        for parser in parsers:
            try:
                parser.find_projects()
            except Exception as e:
                logger.error(
                    f"Ошибка в парсере {parser.__class__.__name__}: {e}"
                )
                notify_user(f"Ошибка парсера: {parser.__class__.__name__}")
                
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        notify_user(f"Критическая ошибка: {e}")

async def async_job():
    """Асинхронная версия основной функции"""
    logger.info("🔍 Запускаю асинхронный поиск заказов...")
    
    parsers = [
        ("FreelanceRu", FreelanceRuParser()),
        ("FLRu", FLRuParser()),
        ("KworkRu", KworkRuParser()),
        ("Upwork", UpworkParser()),
    ]
    
    try:
        # Запускаем все парсеры параллельно
        tasks = []
        for name, parser in parsers:
            logger.info(f"Запускаю парсер {name}...")
            tasks.append(parser.async_find_projects())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Логируем результаты
        for (name, _), result in zip(parsers, results):
            if isinstance(result, Exception):
                logger.error(f"Ошибка в парсере {name}: {str(result)}", exc_info=result)
            elif result is not None:
                logger.info(f"Парсер {name} нашел {len(result) if isinstance(result, list) else 0} проектов")
        
    except Exception as e:
        logger.critical(f"Асинхронная ошибка: {e}", exc_info=True)
        notify_user(f"Асинхронная ошибка: {e}")

def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    if CRON_EXPRESSION:
        trigger = CronTrigger.from_crontab(CRON_EXPRESSION)
        scheduler.add_job(async_job, trigger)
    else:
        scheduler.add_job(async_job, "interval", minutes=PARSING_INTERVAL)
    return scheduler


async def main() -> None:
    scheduler = create_scheduler()
    scheduler.start()

    application = create_application()
    await application.initialize()
    await application.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    # Запускаем асинхронную версию по умолчанию
    asyncio.run(main())
