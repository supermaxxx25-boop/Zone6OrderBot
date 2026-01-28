import os
from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8348647959  # mets TON vrai ID

# =========================
# START
# =========================
async def start(update, context):
    bouton = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Ouvrir la boutique", callback_data="open_shop")]
    ])

    await update.message.reply_text(
        "👋 Bienvenue sur *Zone 6 Food* 🍽️\n\n"
        "Clique sur le bouton ci-dessous pour voir la boutique 👇",
        parse_mode="Markdown",
        reply_markup=bouton
    )

# =========================
# BOUTIQUE
# =========================
async def open_shop(update, context):
    query = update.callback_query
    await query.answer()

    clavier = ReplyKeyboardMarkup(
        [["🍔 Burger", "🍕 Pizza"], ["🍚 Riz poulet"]],
        resize_keyboard=True
    )

    await query.message.reply_text(
        "🍽️ *Menu Zone 6 Food*\n\n"
        "🍔 Burger + frites – 3 500 FCFA\n"
        "🍕 Pizza – 5 000 FCFA\n"
        "🍚 Riz sauce poulet – 4 000 FCFA\n\n"
        "👉 Choisis un plat",
        parse_mode="Markdown",
        reply_markup=clavier
    )

# =========================
# CHOIX DU PLAT
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
            context.user_data["etat"] = "attente_infos"

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

# =========================
# FINALISATION
# =========================
async def finaliser_commande(update, context):
    if context.user_data.get("etat") != "attente_infos":
        return

    infos = update.message.text
    produit = context.user_data["commande"]

    # Client
    await update.message.reply_text(
        "✅ *Commande confirmée !*\n\n"
        f"🍽️ Plat : {produit}\n"
        f"📍 Infos : {infos}\n\n"
        "💵 Paiement à la livraison\n"
        "⏱️ Livraison en cours.\nMerci 🙏",
        parse_mode="Markdown"
    )

    # Admin
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
    app.add_handler(CallbackQueryHandler(open_shop, pattern="open_shop"))

    # ⚠️ ordre crucial
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, finaliser_commande))

    print("✅ Bot en ligne")
    app.run_polling()

if __name__ == "__main__":
    main()
