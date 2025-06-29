import logging
import html
from typing import Optional
from telegram import Bot as TelegramBot
from telegram.ext import Application
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from utils import storage

logger = logging.getLogger(__name__)
_sent_links = storage.load_sent_links()
_application: Optional[Application] = None


def set_application(app: Application) -> None:
    """Set the application instance to use for sending messages."""
    global _application
    _application = app


def _get_bot() -> TelegramBot:
    """Return a bot instance from the application or create one if needed."""
    if _application is None or getattr(_application, "bot", None) is None:
        logger.warning(
            "Application or bot is not initialized, creating Bot instance"
        )
        return TelegramBot(TELEGRAM_TOKEN)
    return _application.bot

async def notify_start() -> None:
    """Send a bot-started notification."""
    if TELEGRAM_CHAT_ID:
        try:
            bot = _get_bot()
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="\uD83E\uDD16 Бот запущен")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления о старте: {e}")

async def notify_stop() -> None:
    """Send a bot-stopped notification."""
    if TELEGRAM_CHAT_ID:
        try:
            bot = _get_bot()
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="\u23F9\uFE0F Бот остановлен")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления об остановке: {e}")

async def notify_user(project):
    """Отправляет уведомление о новом проекте в Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Ошибка: Не указаны токен или chat_id для Telegram")
        return

    link = project.get('link')
    if link in _sent_links:
        logger.info(f"Ссылка уже отправлена: {link}")
        return

    title = html.escape(project['title'])
    description = html.escape(project['description'])

    message = (
        f"<b>🔹 Новый заказ:</b> {title}\n"
        f"🔗 <a href=\"{project['link']}\">Ссылка на заказ</a>\n"
        f"<b>📝 Описание:</b> {description}\n\n"
        f"💬 Для управления ключевыми словами используйте команды:\n"
        "/addkeyword - добавить ключевое слово\n"
        "/removekeyword - удалить ключевое слово\n"
        "/list - показать список ключевых слов"
    )
    
    try:
        bot = _get_bot()
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info(f"Уведомление отправлено: {project['title']}")
        _sent_links.add(link)
        storage.save_sent_link(link)

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        raise
