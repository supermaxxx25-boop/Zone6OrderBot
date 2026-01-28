import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters
)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8348647959  # ⚠️ remplace si besoin par TON vrai ID

# =========================
# COMMANDES
# =========================
async def start(update, context):
    await update.message.reply_text("✅ Bot en ligne ! Tape /boutique pour commander.")

    # Test admin (tu peux supprimer plus tard)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="🧪 Bot démarré avec succès"
    )


async def boutique(update, context):
    clavier = ReplyKeyboardMarkup(
        [["🍔 Burger", "🍕 Pizza"], ["🍚 Riz poulet"]],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🍽️ *Menu Zone 6 Food*\n\n"
        "🍔 Burger + frites – 3 500 FCFA\n"
        "🍕 Pizza – 5 000 FCFA\n"
        "🍚 Riz sauce poulet – 4 000 FCFA\n\n"
        "👉 Choisis un plat",
        parse_mode="Markdown",
        reply_markup=clavier
    )

# =========================
# COMMANDE
# =========================
async def handle_order(update, context):
    text = update.message.text

    produits = {
        "Burger": ("Burger + frites", "3 500 FCFA"),
        "Pizza": ("Pizza", "5 000 FCFA"),
        "Riz": ("Riz sauce poulet", "4 000 FCFA"),
    }

    for key, (produit, prix) in produits.items():
        if key in text:
            context.user_data.clear()
            context.user_data["commande"] = produit

            await update.message.reply_text(
                f"🛒 *Commande :* {produit}\n"
                f"💰 *Prix :* {prix}\n\n"
                "📍 Envoie maintenant :\n"
                "• Adresse\n"
                "• Téléphone\n\n"
                "💵 Paiement à la livraison",
                parse_mode="Markdown"
            )
            return


async def finaliser_commande(update, context):
    if "commande" not in context.user_data:
        return

    infos = update.message.text
    produit = context.user_data["commande"]

    # Message client
    await update.message.reply_text(
        "✅ *Commande confirmée !*\n\n"
        f"🍽️ Plat : {produit}\n"
        f"📍 Infos : {infos}\n\n"
        "💵 Paiement à la livraison\n"
        "⏱️ Livraison en cours.\nMerci 🙏",
        parse_mode="Markdown"
    )

    # Message ADMIN
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📦 *NOUVELLE COMMANDE*\n\n"
            f"👤 Client : @{update.effective_user.username}\n"
            f"🍽️ Plat : {produit}\n"
            f"📍 Infos : {infos}"
        ),
        parse_mode="Markdown"
    )

    context.user_data.clear()

# =========================
# MAIN
# =========================
def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN manquant")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("boutique", boutique))

    # ⚠️ ordre IMPORTANT
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, finaliser_commande))

    print("✅ Bot en ligne")
    app.run_polling()


if __name__ == "__main__":
    main()
