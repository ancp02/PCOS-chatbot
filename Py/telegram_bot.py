from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os

#getting token from environment variable for security
TOKEN = os.getenv("8099554639:AAHPOoT2uWuV9Oek-Lv6n9fQs_CPHl6Hmbc")

# --- Command Handlers ---
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Hello! I'm your PCOS Info Bot.\n"
        "Type /help to see what I can do!"
    )

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📋 Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show help info\n"
        "/PCOS_symptoms - Get info about PCOS symptoms\n"
        "/cure - Learn about PCOS treatment\n"
        "/cause - Understand PCOS causes\n"
        "/longterm_side_effects - Know the long-term side effects"
    )

def pcos_symptoms(update: Update, context: CallbackContext):
    update.message.reply_text(
        "💡 PCOS Symptoms:\n"
        "- Irregular periods\n"
        "- Excess hair growth (hirsutism)\n"
        "- Acne\n"
        "- Weight gain\n"
        "- Thinning hair\n"
        "- Difficulty getting pregnant"
    )

def cure(update: Update, context: CallbackContext):
    update.message.reply_text(
        "💊 PCOS Treatment:\n"
        "There is no permanent cure, but symptoms can be managed with:\n"
        "- Healthy diet + regular exercise\n"
        "- Hormonal birth control\n"
        "- Medication for insulin resistance\n"
        "- Fertility treatments if needed"
    )

def cause(update: Update, context: CallbackContext):
    update.message.reply_text(
        "⚠️ PCOS Causes:\n"
        "The exact cause is unknown. Factors include:\n"
        "- Insulin resistance\n"
        "- Hormonal imbalance\n"
        "- Genetic predisposition"
    )

def longterm_side_effects(update: Update, context: CallbackContext):
    update.message.reply_text(
        "⏳ Long-term Side Effects of PCOS:\n"
        "- Type 2 diabetes risk\n"
        "- Heart disease\n"
        "- Endometrial cancer\n"
        "- Infertility\n"
        "- Mental health challenges (depression, anxiety)"
    )

# --- Main ---
def main():
    if not TOKEN:
        print("❌ BOT_TOKEN environment variable is missing!")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Register handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("PCOS_symptoms", pcos_symptoms))
    dp.add_handler(CommandHandler("cure", cure))
    dp.add_handler(CommandHandler("cause", cause))
    dp.add_handler(CommandHandler("longterm_side_effects", longterm_side_effects))

    # Start
    updater.start_polling()
    print("🚀 Bot is running... Press Ctrl+C to stop.")
    updater.idle()

if __name__ == '__main__':
    main()
