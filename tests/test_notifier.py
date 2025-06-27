import logging
from utils.notifier import notify_user

class DummyResponse:
    def raise_for_status(self):
        pass


def test_notify_user_escaping(monkeypatch, tmp_path):
    sent = {}

    def mock_post(url, data):
        sent.update(data)
        return DummyResponse()

    import utils.notifier as notifier
    monkeypatch.setattr('requests.post', mock_post, raising=False)
    # disable logging output
    logging.getLogger('utils.notifier').disabled = True
    monkeypatch.setattr(notifier, 'SENT_LINKS_FILE', tmp_path / 'links.txt', raising=False)
    monkeypatch.setattr(notifier, '_sent_links', set(), raising=False)
    project = {
        'title': '<b>Title</b>',
        'link': 'http://example.com',
        'description': '<i>Description</i>'
    }
    notify_user(project)
    assert '&lt;b&gt;Title&lt;/b&gt;' in sent['text']
    assert '&lt;i&gt;Description&lt;/i&gt;' in sent['text']


def test_notify_user_duplicate(monkeypatch, tmp_path):
    sent = []

    def mock_post(url, data):
        sent.append(data)
        return DummyResponse()

    import utils.notifier as notifier
    monkeypatch.setattr('requests.post', mock_post, raising=False)
    logging.getLogger('utils.notifier').disabled = True
    monkeypatch.setattr(notifier, 'SENT_LINKS_FILE', tmp_path / 'links.txt', raising=False)
    monkeypatch.setattr(notifier, '_sent_links', set(), raising=False)

    project = {'title': 't', 'link': 'http://dup', 'description': 'd'}
    notifier.notify_user(project)
    notifier.notify_user(project)
    assert len(sent) == 1
