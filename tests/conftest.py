import os
import sys
import types
import pytest
import xml.etree.ElementTree as ET

# Ensure repository root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Provide dummy env vars so importing `config` does not fail
os.environ.setdefault("TELEGRAM_TOKEN", "dummy")
os.environ.setdefault("TELEGRAM_CHAT_ID", "dummy")

# Provide a stub for `dotenv` if the package is missing
try:
    import dotenv  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    dotenv = types.ModuleType("dotenv")
    sys.modules["dotenv"] = dotenv
    def load_dotenv(_path=None):
        return None
    dotenv.load_dotenv = load_dotenv

# Stub `requests` if missing
try:
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    requests = types.ModuleType("requests")
    sys.modules["requests"] = requests
    class HTTPError(Exception):
        pass
    requests.HTTPError = HTTPError
    def _not_implemented(*a, **k):
        raise RuntimeError("network disabled")
    requests.get = _not_implemented

# Stub `telegram` if missing
try:
    import telegram  # type: ignore
    import telegram.ext  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    telegram = types.ModuleType("telegram")
    sys.modules["telegram"] = telegram

    class Bot:  # type: ignore
        def __init__(self, *a, **k):
            pass
        def send_message(self, *a, **k):
            pass

    class Update:  # type: ignore
        pass

    class InlineKeyboardButton:  # type: ignore
        def __init__(self, text, callback_data=None, url=None):
            self.text = text
            self.callback_data = callback_data
            self.url = url

    class InlineKeyboardMarkup:  # type: ignore
        def __init__(self, keyboard):
            self.inline_keyboard = keyboard

    telegram.Bot = Bot
    telegram.Update = Update
    telegram.InlineKeyboardButton = InlineKeyboardButton
    telegram.InlineKeyboardMarkup = InlineKeyboardMarkup

    request_mod = types.ModuleType("telegram.request")
    sys.modules["telegram.request"] = request_mod

    class HTTPXRequest:  # type: ignore
        def __init__(self, *a, **k):
            pass

    request_mod.HTTPXRequest = HTTPXRequest

    ext = types.ModuleType("telegram.ext")
    sys.modules["telegram.ext"] = ext

    class Application:  # type: ignore
        async def initialize(self):
            pass
        async def start(self):
            pass
        async def stop(self):
            pass
        async def shutdown(self):
            pass
        def add_handler(self, *a, **k):
            pass

    class ApplicationBuilder:  # type: ignore
        def token(self, _):
            return self
        def build(self):
            return Application()

    class CommandHandler:  # type: ignore
        def __init__(self, *a, **k):
            pass

    class CallbackQueryHandler:  # type: ignore
        def __init__(self, *a, **k):
            pass

    class ContextTypes:  # type: ignore
        DEFAULT_TYPE = object

    ext.ApplicationBuilder = ApplicationBuilder
    ext.Application = Application
    ext.CommandHandler = CommandHandler
    ext.CallbackQueryHandler = CallbackQueryHandler
    ext.ContextTypes = ContextTypes
# Stub `aiohttp` if missing
try:
    import aiohttp  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    aiohttp = types.ModuleType("aiohttp")
    sys.modules["aiohttp"] = aiohttp
    class ClientSession:  # type: ignore
        pass
    class ClientConnectorError(Exception):
        pass
    class TCPConnector:
        def __init__(self, *a, **k):
            pass
    aiohttp.ClientSession = ClientSession
    aiohttp.ClientConnectorError = ClientConnectorError
    aiohttp.TCPConnector = TCPConnector

# Stub `certifi` if missing
try:
    import certifi  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    certifi = types.ModuleType("certifi")
    sys.modules["certifi"] = certifi
    certifi.where = lambda: ""

# Stub `apscheduler` if missing
try:
    import apscheduler  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    apscheduler = types.ModuleType("apscheduler")
    sys.modules["apscheduler"] = apscheduler
    schedulers = types.ModuleType("apscheduler.schedulers")
    asyncio_sched = types.ModuleType("apscheduler.schedulers.asyncio")
    triggers = types.ModuleType("apscheduler.triggers")
    cron = types.ModuleType("apscheduler.triggers.cron")
    sys.modules["apscheduler.schedulers"] = schedulers
    sys.modules["apscheduler.schedulers.asyncio"] = asyncio_sched
    sys.modules["apscheduler.triggers"] = triggers
    sys.modules["apscheduler.triggers.cron"] = cron

    class AsyncIOScheduler:  # type: ignore
        def __init__(self, *a, **k):
            pass

        def add_job(self, *a, **k):
            pass

        def start(self):
            pass

    class CronTrigger:  # type: ignore
        @classmethod
        def from_crontab(cls, expr):
            return cls()

    asyncio_sched.AsyncIOScheduler = AsyncIOScheduler
    cron.CronTrigger = CronTrigger

# Minimal implementation of BeautifulSoup for our tests
try:
    from bs4 import BeautifulSoup  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    pass

def _find_by_classes(element, classes):
    results = []
    for el in element.iter():
        class_attr = el.attrib.get("class", "")
        if all(c in class_attr.split() for c in classes):
            results.append(el)
    return results

def _descend(nodes, token):
    if token.startswith('.'):
        classes = token.strip('.').split('.')
        found = []
        for node in nodes:
            found.extend(_find_by_classes(node, classes))
        return found
    else:
        if '.' in token:
            tag, *cls = token.split('.')
        else:
            tag, cls = token, []
        found = []
        for node in nodes:
            for el in node.iter(tag):
                class_attr = el.attrib.get("class", "")
                if all(c in class_attr.split() for c in cls):
                    found.append(el)
        return found

class _FakeTag:
    def __init__(self, element):
        self._el = element
    def select(self, selector):
        tokens = selector.split()
        nodes = [self._el]
        for token in tokens:
            nodes = _descend(nodes, token)
        return [_FakeTag(n) for n in nodes]
    def select_one(self, selector):
        res = self.select(selector)
        return res[0] if res else None

    @property
    def text(self):
        return ''.join(self._el.itertext())

    def __getitem__(self, item):
        return self._el.attrib[item]

class BeautifulSoup:  # type: ignore
    def __init__(self, html, parser='html.parser'):
        self._root = ET.fromstring(f"<root>{html}</root>")
    def select(self, selector):
        tokens = selector.split()
        nodes = [self._root]
        for token in tokens:
            nodes = _descend(nodes, token)
        return [_FakeTag(n) for n in nodes]
    def select_one(self, selector):
        res = self.select(selector)
        return res[0] if res else None

sys.modules['bs4'] = types.ModuleType('bs4')
sys.modules['bs4'].BeautifulSoup = BeautifulSoup

class _DummyResponse:
    def __init__(self, text: str = "", status: int = 200):
        self.status = status
        self._text = text
    async def text(self) -> str:
        return self._text
    def raise_for_status(self) -> None:
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass

class _DummySession:
    def __init__(self, text: str = ""):
        self._text = text
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
    def get(self, *args, **kwargs):
        return _DummyResponse(self._text)

# Patch aiohttp.ClientSession globally to prevent real HTTP calls
@pytest.fixture(autouse=True)
def _patch_aiohttp(monkeypatch):
    monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: _DummySession(), raising=False)
    yield
