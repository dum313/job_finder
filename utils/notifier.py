import logging
import html
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from utils import storage

logger = logging.getLogger(__name__)
_sent_links = storage.load_sent_links()

def notify_user(project):
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
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        logger.info(f"Уведомление отправлено: {project['title']}")
        _sent_links.add(link)
        storage.save_sent_link(link)

    except requests.RequestException as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
