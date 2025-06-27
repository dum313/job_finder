import logging
from utils.notifier import notify_user

class DummyResponse:
    def raise_for_status(self):
        pass


def test_notify_user_escaping(monkeypatch):
    sent = {}

    def mock_post(url, data):
        sent.update(data)
        return DummyResponse()

    monkeypatch.setattr('requests.post', mock_post, raising=False)
    # disable logging output
    logging.getLogger('utils.notifier').disabled = True
    project = {
        'title': '<b>Title</b>',
        'link': 'http://example.com',
        'description': '<i>Description</i>'
    }
    notify_user(project)
    assert '&lt;b&gt;Title&lt;/b&gt;' in sent['text']
    assert '&lt;i&gt;Description&lt;/i&gt;' in sent['text']
