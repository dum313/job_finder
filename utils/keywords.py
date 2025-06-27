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
    or DEFAULT_KEYWORDS
)

EXCLUDE_WORDS = (
    _load_list_from_file(os.getenv('EXCLUDE_WORDS_FILE', ''))
    or _load_list_from_env('EXCLUDE_WORDS')
    or DEFAULT_EXCLUDE_WORDS
)
