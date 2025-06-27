import asyncio
import os
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from parsers.freelance_ru import FreelanceRuParser
from parsers.fl_ru import FLRuParser
from parsers.kwork_ru import KworkRuParser
from parsers.upwork import UpworkParser
from utils.notifier import notify_user, set_application
from utils.telegram_bot import create_application
from utils import storage
from config import (
    PARSING_INTERVAL,
    CRON_EXPRESSION,
    TIMEZONE,
    LOG_FILES,
    setup_logger
)

# Настройка логирования
logger = setup_logger(__name__, LOG_FILES['bot'])
logger.info("=" * 50)
logger.info("Starting application")
logger.info("=" * 50)

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
    application = None
    scheduler = None
    
    try:
        logger.info("Initializing storage...")
        storage.init()
        logger.info("Starting application...")
        
        # Create and start scheduler
        logger.info("Creating scheduler...")
        scheduler = create_scheduler()
        logger.info("Starting scheduler...")
        scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Create and start Telegram application
        logger.info("Creating Telegram application...")
        application = create_application()
        logger.info("Initializing notifier with application...")
        set_application(application)
        
        logger.info("Initializing Telegram application...")
        await application.initialize()
        
        logger.info("Starting Telegram application...")
        await application.start()
        
        logger.info("Setting up bot commands...")
        try:
            await application.bot.set_my_commands([
                ("start", "Запустить бота"),
                ("addkeyword", "Добавить ключевое слово"),
                ("removekeyword", "Удалить ключевое слово"),
                ("list", "Список ключевых слов")
            ])
            logger.info("Bot commands set up successfully")
        except Exception as e:
            logger.error(f"Failed to set bot commands: {e}", exc_info=True)
        
        logger.info("Telegram application started successfully")
        
        # Run the job immediately on startup
        logger.info("Running initial job...")
        try:
            await async_job()
            logger.info("Initial job completed successfully")
        except Exception as e:
            logger.error(f"Error in initial job: {e}", exc_info=True)
        
        logger.info("Bot is now running. Press Ctrl+C to stop.")
        
        # Keep the application running
        await asyncio.Event().wait()
        
    except asyncio.CancelledError:
        logger.info("Shutting down...")
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}", exc_info=True)
        raise
    finally:
        # Cleanup
        if scheduler:
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
        
        if application and application.running:
            logger.info("Stopping Telegram application...")
            await application.stop()
            logger.info("Telegram application stopped")

if __name__ == "__main__":
    # Запускаем асинхронную версию по умолчанию
    asyncio.run(main())
