# Список ключевых слов для поиска заказов по умолчанию
DEFAULT_KEYWORDS = [
    # Основные слова
    'сайт',
    'лендинг',
    'веб',
    'html',
    'css',
    'верстка',
    'фриланс',
    'web',
    'website',

    # Типы сайтов
    'одностраничник',
    'портфолио',
    'визитка',
    'каталог',
    'корпоративный',

    # Технологии
    'bootstrap',
    'wordpress',
    'joomla',
    'tilda',
    'wix',

    # Дизайн
    'адаптивный',
    'мобильная',
    'ui',
    'ux',
    'интерфейс'
]

# Слова для исключения (можно добавить нежелательные заказы) по умолчанию
DEFAULT_EXCLUDE_WORDS = [
    'сопровождение',
    'исправление',
    'доработка',
    'тестирование',
    'seo',
    'smm'
]

import os
from pathlib import Path
from . import storage


def _load_list_from_file(file_path: str) -> list[str] | None:
    path = Path(file_path)
    if path.exists():
        try:
            with path.open('r', encoding='utf-8') as fh:
                return [line.strip() for line in fh if line.strip()]
        except Exception:
            return None
    return None


def _load_list_from_env(var_name: str) -> list[str] | None:
    value = os.getenv(var_name)
    if value:
        return [v.strip() for v in value.split(',') if v.strip()]
    return None


KEYWORDS = (
    _load_list_from_file(os.getenv('KEYWORDS_FILE', ''))
    or _load_list_from_env('KEYWORDS')
    or list(DEFAULT_KEYWORDS)
)

EXCLUDE_WORDS = (
    _load_list_from_file(os.getenv('EXCLUDE_WORDS_FILE', ''))
    or _load_list_from_env('EXCLUDE_WORDS')
    or list(DEFAULT_EXCLUDE_WORDS)
)

# Override with values stored in the database if present
stored_inc = storage.load_keywords(True)
if stored_inc:
    KEYWORDS = list(stored_inc)
stored_exc = storage.load_keywords(False)
if stored_exc:
    EXCLUDE_WORDS = list(stored_exc)


def add_keyword(word: str) -> None:
    """Add a keyword and persist it."""
    word = word.strip().lower()
    if word and word not in KEYWORDS:
        KEYWORDS.append(word)
        storage.save_keyword(word, True)


def remove_keyword(word: str) -> None:
    """Remove a keyword and update storage."""
    word = word.strip().lower()
    if word in KEYWORDS:
        KEYWORDS.remove(word)
        storage.delete_keyword(word, True)
