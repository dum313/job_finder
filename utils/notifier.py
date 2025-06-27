import logging
import html
from telegram import Bot as TelegramBot
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from utils import storage

logger = logging.getLogger(__name__)
_sent_links = storage.load_sent_links()
_bot: TelegramBot | None = None


def _get_bot() -> TelegramBot:
    global _bot
    if _bot is None:
        _bot = TelegramBot(token=TELEGRAM_TOKEN)
    return _bot

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
        f"🔗 <a href=\"{project['link']}\">{project['link']}</a>\n"
        f"<b>📝 Описание:</b> {description}"
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
