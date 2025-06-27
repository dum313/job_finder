import logging
import asyncio
from utils.notifier import notify_user

def test_notify_user_escaping(monkeypatch, tmp_path):
    sent = {}

    async def mock_send(self, chat_id, text, parse_mode=None, disable_web_page_preview=None):
        sent['chat_id'] = chat_id
        sent['text'] = text
        sent['parse_mode'] = parse_mode

    import utils.notifier as notifier
    monkeypatch.setattr('telegram.Bot.send_message', mock_send, raising=False)
    # disable logging output
    logging.getLogger('utils.notifier').disabled = True
    notifier.storage.init(tmp_path / 'links.db')
    monkeypatch.setattr(notifier, '_sent_links', set(), raising=False)
    project = {
        'title': '<b>Title</b>',
        'link': 'http://example.com',
        'description': '<i>Description</i>'
    }
    asyncio.run(notify_user(project))
    assert '&lt;b&gt;Title&lt;/b&gt;' in sent['text']
    assert '&lt;i&gt;Description&lt;/i&gt;' in sent['text']


def test_notify_user_duplicate(monkeypatch, tmp_path):
    sent = []

    async def mock_send(self, chat_id, text, parse_mode=None, disable_web_page_preview=None):
        sent.append(text)

    import utils.notifier as notifier
    monkeypatch.setattr('telegram.Bot.send_message', mock_send, raising=False)
    logging.getLogger('utils.notifier').disabled = True
    notifier.storage.init(tmp_path / 'links.db')
    monkeypatch.setattr(notifier, '_sent_links', set(), raising=False)

    project = {'title': 't', 'link': 'http://dup', 'description': 'd'}
    asyncio.run(notifier.notify_user(project))
    # simulate new run by clearing in-memory cache and reloading from DB
    notifier._sent_links = notifier.storage.load_sent_links()
    asyncio.run(notifier.notify_user(project))
    assert len(sent) == 1
