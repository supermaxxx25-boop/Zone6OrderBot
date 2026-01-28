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

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN manquant")

if not ADMIN_ID:
    raise RuntimeError("❌ ADMIN_ID manquant")

ADMIN_ID = int(ADMIN_ID)

# =========================
# /start
# =========================
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

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "🍽️ *Zone 6 Food*\n\n"
            "Clique sur le bouton ci-dessous pour commander 👇"
        ),
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# =========================
# RÉCEPTION DES DONNÉES MINI APP
# =========================
async def webapp_data(update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user

    try:
        data = update.message.web_app_data.data
        panier = json.loads(data)
    except Exception:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Erreur lors de la réception de la commande."
        )
        return

    # -------- Confirmation client --------
    message_client = "✅ *Commande confirmée !*\n\n"

    for plat, qte in panier.items():
        message_client += f"• {plat} × {qte}\n"

    message_client += "\n💵 Paiement à la livraison\n⏱️ Livraison en cours"

    await context.bot.send_message(
        chat_id=chat_id,
        text=message_client,
        parse_mode="Markdown"
    )

    # -------- Notification admin --------
    message_admin = (
        "🧾 *Nouvelle commande Mini App*\n\n"
        f"👤 Client : {user.first_name or 'Inconnu'}\n"
        f"🆔 ID client : `{user.id}`\n\n"
    )

    for plat, qte in panier.items():
        message_admin += f"• {plat} × {qte}\n"

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=message_admin,
        parse_mode="Markdown"
    )

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Handler CRITIQUE pour Mini App
    app.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data)
    )

    print("🤖 Bot lancé avec succès")
    app.run_polling()

if __name__ == "__main__":
    main()
