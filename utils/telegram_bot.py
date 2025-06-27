import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.request import HTTPXRequest
from types import SimpleNamespace
from config import TELEGRAM_TOKEN
from .keywords import KEYWORDS, add_keyword, remove_keyword


async def addkeyword_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /addkeyword <word>")
        return
    word = context.args[0]
    add_keyword(word)
    await update.message.reply_text(f"Added keyword: {word}")


async def removekeyword_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /removekeyword <word>")
        return
    word = context.args[0]
    remove_keyword(word)
    await update.message.reply_text(f"Removed keyword: {word}")


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(", ".join(KEYWORDS))


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("Add keyword", callback_data="addkeyword")],
        [InlineKeyboardButton("Remove keyword", callback_data="removekeyword")],
        [InlineKeyboardButton("List keywords", callback_data="list")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome! Use the buttons below to manage keywords.",
        reply_markup=markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    dummy_update = SimpleNamespace(message=query.message)
    if query.data == "addkeyword":
        await addkeyword_cmd(dummy_update, context)
    elif query.data == "removekeyword":
        await removekeyword_cmd(dummy_update, context)
    elif query.data == "list":
        await list_cmd(dummy_update, context)


def create_application():
    # Создаем кастомный HTTP-клиент с увеличенными таймаутами
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30.0,
        write_timeout=30.0,
        connect_timeout=30.0,
        pool_timeout=30.0,
    )
    
    # Настраиваем приложение
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .request(request)  # Таймауты уже заданы в request
        .build()
    )
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("addkeyword", addkeyword_cmd))
    app.add_handler(CommandHandler("removekeyword", removekeyword_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Настраиваем логирование
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    return app
