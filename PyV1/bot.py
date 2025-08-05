from dotenv import load_dotenv, find_dotenv

# This finds your .env file in the current directory or any parent and loads it
load_dotenv(find_dotenv())

# PyV1/bot.py

import os, logging, asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from retrieval import search  # Import your search function

# 1. Load Telegram Bot Token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Please set TELEGRAM_BOT_TOKEN environment variable")

# 2. Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 3. /start command
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Ask me any question about PCOS."
    )

# 4. /help command
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Type your question about PCOS (symptoms, diagnosis, treatment) and I'll answer!"
    )

# 5. Message handler
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_q = update.message.text
    # a. Retrieve relevant passages
    results = search(user_q, top_k=3)
    # b. Prepare response
    if results:
        response = "\n\n".join(results)
    else:
        response = "Sorry, I don't have information on that. Try another question!"
    # c. Send reply
    await update.message.reply_text(response)

# 6. Main entrypoint
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    logger.info("Bot is up and running!")
    app.run_polling()  # <-- Correct way to start and poll

if __name__ == "__main__":
    main()

