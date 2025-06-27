import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def notify_user(project):
    """Отправляет уведомление о новом проекте в Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Ошибка: Не указаны токен или chat_id для Telegram")
        return
    
    message = (
        f"<b>🔹 Новый заказ:</b> {project['title']}\n"
        f"🔗 <a href=\"{project['link']}\">{project['link']}</a>\n"
        f"<b>📝 Описание:</b> {project['description']}"
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
        print(f"Уведомление отправлено: {project['title']}")
    
    except requests.RequestException as e:
        print(f"Ошибка при отправке сообщения: {e}")
