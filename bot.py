import os
from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8348647959  # mets TON vrai ID

# États de conversation
CHOIX_PRODUIT, INFOS_CLIENT = range(2)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bouton = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Ouvrir la boutique", callback_data="open_shop")]
    ])

    await update.message.reply_text(
        "👋 Bienvenue sur *Zone 6 Food* 🍽️\n\n"
        "Clique sur le bouton ci-dessous pour commander 👇",
        parse_mode="Markdown",
        reply_markup=bouton
    )

# =========================
# BOUTIQUE
# =========================
async def open_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    return CHOIX_PRODUIT

# =========================
# CHOIX DU PRODUIT
# =========================
async def choix_produit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    produits = {
        "Burger": ("Burger + frites", "3 500 FCFA"),
        "Pizza": ("Pizza", "5 000 FCFA"),
        "Riz": ("Riz sauce poulet", "4 000 FCFA"),
    }

    for key, (produit, prix) in produits.items():
        if key in text:
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
            return INFOS_CLIENT

    await update.message.reply_text("❌ Merci de choisir un plat du menu.")
    return CHOIX_PRODUIT

# =========================
# FINALISATION
# =========================
async def finaliser_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    infos = update.message.text
    produit = context.user_data.get("commande")

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
    return ConversationHandler.END

# =========================
# MAIN
# =========================
def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN manquant")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(open_shop, pattern="open_shop")],
        states={
            CHOIX_PRODUIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choix_produit)],
            INFOS_CLIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, finaliser_commande)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("✅ Bot en ligne")
    app.run_polling()

if __name__ == "__main__":
    main()
