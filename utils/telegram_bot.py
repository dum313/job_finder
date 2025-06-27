from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from types import SimpleNamespace

try:  # telegram may be stubbed in tests
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import CallbackQueryHandler
except Exception:  # pragma: no cover - fallback for missing library
    class InlineKeyboardButton:  # type: ignore
        def __init__(self, text: str, callback_data: str | None = None):
            self.text = text
            self.callback_data = callback_data

    class InlineKeyboardMarkup:  # type: ignore
        def __init__(self, keyboard):
            self.inline_keyboard = keyboard

    class CallbackQueryHandler:  # type: ignore
        def __init__(self, callback, *a, **k):
            self.callback = callback
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
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("addkeyword", addkeyword_cmd))
    app.add_handler(CommandHandler("removekeyword", removekeyword_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    return app
