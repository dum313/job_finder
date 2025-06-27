import logging
import sqlite3
from pathlib import Path
from typing import Set

logger = logging.getLogger(__name__)

DB_FILE = Path('sent_links.db')
_conn: sqlite3.Connection | None = None


def init(db_path: Path | str | None = None) -> None:
    """Initialize connection to the SQLite database."""
    global DB_FILE, _conn
    if db_path is not None:
        DB_FILE = Path(db_path)
    if _conn is not None:
        try:
            _conn.close()
        except Exception:
            pass
        _conn = None
    _conn = sqlite3.connect(DB_FILE)
    _conn.execute(
        "CREATE TABLE IF NOT EXISTS sent_links (link TEXT PRIMARY KEY)"
    )
    _conn.commit()


def _get_conn() -> sqlite3.Connection:
    if _conn is None:
        init()
    assert _conn is not None
    return _conn


def load_sent_links() -> Set[str]:
    """Return a set of previously sent links."""
    conn = _get_conn()
    cur = conn.execute("SELECT link FROM sent_links")
    return {row[0] for row in cur.fetchall()}


def save_sent_link(link: str) -> None:
    """Persist a new sent link if it's not already stored."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO sent_links(link) VALUES (?)",
            (link,),
        )
        conn.commit()
    except Exception:
        logger.warning("Не удалось сохранить отправленную ссылку")

init()
