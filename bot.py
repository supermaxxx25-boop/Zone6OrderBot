from telegram.ext import ApplicationBuilder, CommandHandler
import os

TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("✅ Bot en ligne !")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN manquant")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
