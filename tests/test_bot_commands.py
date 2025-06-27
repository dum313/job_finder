import asyncio
from utils import keywords
from utils import telegram_bot

class DummyMessage:
    def __init__(self):
        self.texts = []
    async def reply_text(self, text):
        self.texts.append(text)

class DummyUpdate:
    def __init__(self):
        self.message = DummyMessage()

class DummyContext:
    def __init__(self, args):
        self.args = args


def test_keyword_commands(tmp_path):
    keywords.storage.init(tmp_path / 'db.sqlite')
    keywords.KEYWORDS.clear()
    async def run():
        upd = DummyUpdate()
        await telegram_bot.addkeyword_cmd(upd, DummyContext(['python']))
        assert 'python' in keywords.KEYWORDS
        assert 'python' in keywords.storage.load_keywords(True)

        upd_list = DummyUpdate()
        await telegram_bot.list_cmd(upd_list, DummyContext([]))
        assert 'python' in upd_list.message.texts[0]

        upd_rm = DummyUpdate()
        await telegram_bot.removekeyword_cmd(upd_rm, DummyContext(['python']))
        assert 'python' not in keywords.KEYWORDS
        assert 'python' not in keywords.storage.load_keywords(True)
        keywords.KEYWORDS[:] = keywords.DEFAULT_KEYWORDS[:]
        keywords.storage.init('sent_links.db')
    asyncio.run(run())
