import asyncio
from utils import keywords
from utils import telegram_bot

class DummyMessage:
    def __init__(self):
        self.texts = []
        self.markups = []

    async def reply_text(self, text, reply_markup=None):
        self.texts.append(text)
        self.markups.append(reply_markup)

class DummyUpdate:
    def __init__(self):
        self.message = DummyMessage()
        self.callback_query = None


class DummyCallbackQuery:
    def __init__(self, message, data):
        self.message = message
        self.data = data
        self.answered = False

    async def answer(self):
        self.answered = True

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


def test_start_cmd(tmp_path):
    keywords.storage.init(tmp_path / 'db.sqlite')

    async def run():
        upd = DummyUpdate()
        await telegram_bot.start_cmd(upd, DummyContext([]))
        assert 'welcome' in upd.message.texts[0].lower()

        cq_upd = DummyUpdate()
        cq_upd.callback_query = DummyCallbackQuery(cq_upd.message, 'list')
        await telegram_bot.button_handler(cq_upd, DummyContext([]))
        assert keywords.KEYWORDS[0] in cq_upd.message.texts[0]
        keywords.storage.init('sent_links.db')

    asyncio.run(run())
