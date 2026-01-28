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

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN manquant")

if not ADMIN_ID:
    raise RuntimeError("❌ ADMIN_ID manquant")

ADMIN_ID = int(ADMIN_ID)

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
        "🍽️ *Zone 6 Food*\n\n"
        "Clique sur le bouton ci-dessous pour commander 👇",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ======================
# RÉCEPTION MINI APP
# ======================
async def webapp_data(update, context):
    try:
        data = update.message.web_app_data.data
        panier = json.loads(data)
    except Exception as e:
        await update.message.reply_text("❌ Erreur lors de la réception de la commande.")
        return

    user = update.effective_user

    # -------- Message client --------
    texte_client = "✅ *Commande confirmée !*\n\n"
    for plat, qte in panier.items():
        texte_client += f"• {plat} × {qte}\n"

    texte_client += "\n💵 Paiement à la livraison\n⏱️ Livraison en cours"

    await update.message.reply_text(
        texte_client,
        parse_mode="Markdown"
    )

    # -------- Message admin --------
    texte_admin = (
        "🧾 *Nouvelle commande Mini App*\n\n"
        f"👤 Client : {user.first_name or 'Inconnu'}\n"
        f"🆔 ID client : `{user.id}`\n\n"
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
    app = ApplicationBuilder().token(TOKEN).build()

    # Commandes
    app.add_handler(CommandHandler("start", start))

    # Réception données Mini App (CRITIQUE)
    app.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data)
    )

    print("🤖 Bot lancé et prêt")
    app.run_polling()

if __name__ == "__main__":
    main()
