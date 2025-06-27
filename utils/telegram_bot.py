from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
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


def create_application():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("addkeyword", addkeyword_cmd))
    app.add_handler(CommandHandler("removekeyword", removekeyword_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    return app
