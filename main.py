import logging
import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from parsers.freelance_ru import FreelanceRuParser
from parsers.fl_ru import FLRuParser
from parsers.kwork_ru import KworkRuParser
from parsers.upwork import UpworkParser
from utils.notifier import notify_user
from utils.telegram_bot import create_application
from utils import storage
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

# Выводим переменные окружения для отладки
logger.info("Проверка переменных окружения:")
for var in ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'CRON_EXPRESSION']:
    logger.info(f"{var} = {'установлен' if os.getenv(var) else 'не установлен'}")

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
        
        # Обрабатываем результаты
        for (name, _), result in zip(parsers, results):
            if isinstance(result, Exception):
                logger.error(f"Ошибка в парсере {name}: {str(result)}", exc_info=result)
            elif result and isinstance(result, list):
                logger.info(f"Парсер {name} нашел {len(result)} проектов")
                # Отправляем уведомления о новых проектах
                for project in result:
                    try:
                        await notify_user(project)
                        await asyncio.sleep(1)  # Небольшая задержка между сообщениями
                    except Exception as e:
                        logger.error(f"Ошибка при отправке уведомления: {e}")
            else:
                logger.info(f"Парсер {name} не нашел проектов")
        
    except Exception as e:
        error_msg = f"Асинхронная ошибка: {e}"
        logger.critical(error_msg, exc_info=True)
        try:
            await notify_user({"title": "Ошибка", "description": error_msg, "link": ""})
        except Exception as notify_err:
            logger.error(f"Не удалось отправить уведомление об ошибке: {notify_err}")

def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    
    if CRON_EXPRESSION:
        logger.info(f"Setting up cron job with expression: {CRON_EXPRESSION}")
        try:
            trigger = CronTrigger.from_crontab(CRON_EXPRESSION)
            job = scheduler.add_job(
                async_job,
                trigger,
                id='parse_job',
                name='Parse job',
                replace_existing=True
            )
            logger.info(f"Added cron job: {job}")
        except Exception as e:
            logger.error(f"Error creating cron trigger: {e}")
            logger.info("Falling back to interval-based scheduling")
            scheduler.add_job(
                async_job,
                "interval",
                minutes=PARSING_INTERVAL,
                id='parse_job',
                name='Parse job',
                replace_existing=True
            )
    else:
        logger.info(f"Setting up interval job with {PARSING_INTERVAL} minutes interval")
        scheduler.add_job(
            async_job,
            "interval",
            minutes=PARSING_INTERVAL,
            id='parse_job',
            name='Parse job',
            replace_existing=True
        )
    
    logger.info("Scheduler created with jobs: %s", scheduler.get_jobs())
    return scheduler


async def main() -> None:
    try:
        storage.init()
        logger.info("Starting application...")
        
        # Create and start scheduler
        scheduler = create_scheduler()
        scheduler.start()
        logger.info("Scheduler started")
        
        # Create and start Telegram application
        application = create_application()
        await application.initialize()
        await application.start()
        logger.info("Telegram application started")
        
        # Run the job immediately on startup
        logger.info("Running initial job...")
        await async_job()
        
        # Keep the application running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    # Запускаем асинхронную версию по умолчанию
    asyncio.run(main())
