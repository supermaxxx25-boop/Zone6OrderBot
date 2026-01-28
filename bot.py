import os
import json
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ======================
# /start
# ======================
async def start(update, context):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🛒 Ouvrir la boutique",
                web_app=WebAppInfo(
                    url="https://supermaxxx25-boop.github.io/Zone6OrderBot/"
                )
            )
        ]
    ])

    await update.message.reply_text(
        "🍽️ *Zone 6 Food*\n\nClique pour commander 👇",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ======================
# RÉCEPTION MINI APP
# ======================
async def webapp_data(update, context):
    data = update.message.web_app_data.data
    panier = json.loads(data)

    user = update.effective_user

    # Message client
    texte_client = "✅ *Commande confirmée !*\n\n"
    for plat, qte in panier.items():
        texte_client += f"• {plat} × {qte}\n"

    texte_client += "\n⏱️ Livraison en cours\n💵 Paiement à la livraison"

    await update.message.reply_text(texte_client, parse_mode="Markdown")

    # Message admin
    texte_admin = (
        "🧾 *Nouvelle commande Mini App*\n\n"
        f"👤 Client : {user.first_name}\n"
        f"🆔 ID : `{user.id}`\n\n"
    )

    for plat, qte in panier.items():
        texte_admin += f"• {plat} × {qte}\n"

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=texte_admin,
        parse_mode="Markdown"
    )

# ======================
# MAIN
# ======================
def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN manquant")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data)
    )

    print("🤖 Bot lancé")
    app.run_polling()

if __name__ == "__main__":
    main()
