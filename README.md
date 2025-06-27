# Поисковик заказов на сайты

Приложение на Python, которое автоматически ищет заказы по созданию сайтов на фриланс-платформах и отправляет результаты в Telegram.

## Описание проекта

### Назначение

Автоматизировать поиск работы для фрилансеров и новичков в разработке сайтов. Приложение сканирует заказы на платформе freelance.ru и отправляет подходящие проекты в Telegram каждые 30 минут.

### Функциональность

- Парсинг заказов с fl.ru, freelance.ru и kwork.ru
- Фильтрация заказов по ключевым словам
- Отправка уведомлений в Telegram
- Асинхронный запуск каждые 30 минут

## Структура проекта

```
job_finder/
├── main.py              # Основной запуск
├── parsers/             # Парсеры для разных сайтов
│   ├── fl_ru.py        # Парсинг fl.ru
│   ├── freelance_ru.py # Парсинг freelance.ru
│   └── kwork_ru.py     # Парсинг kwork.ru
├── utils/              # Утилиты
│   ├── notifier.py     # Отправка сообщений
│   └── keywords.py     # Список ключевых слов
├── config.py           # Настройки
└── requirements.txt    # Зависимости
```

## Установка

1. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте Telegram в `.env`:
```bash
echo "TELEGRAM_TOKEN=ваш_токен" > .env
echo "TELEGRAM_CHAT_ID=ваш_chat_id" >> .env
```

4. Запустите бота:
```bash
python main.py
```

По умолчанию приложение запускается в асинхронном режиме.

## Требования

- Python 3.10+
- Бот-токен Telegram
- Telegram chat_id

## Зависимости

- `requests`
- `beautifulsoup4`
