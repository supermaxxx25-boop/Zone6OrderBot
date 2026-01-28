import os
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8348647959  # ⚠️ remplace par TON vrai ID Telegram

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Ouvrir la boutique", callback_data="shop")]
    ])

    await update.message.reply_text(
        "👋 Bienvenue sur *Zone 6 Food* 🍽️\n\n"
        "Clique sur le bouton ci-dessous pour commander 👇",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# =========================
# BOUTIQUE
# =========================
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    menu = ReplyKeyboardMarkup(
        [["🍔 Burger", "🍕 Pizza"], ["🍚 Riz poulet"]],
        resize_keyboard=True
    )

    await query.message.reply_text(
        "🍽️ *Menu*\n\n"
        "🍔 Burger + frites – 3 500 FCFA\n"
        "🍕 Pizza – 5 000 FCFA\n"
        "🍚 Riz poulet – 4 000 FCFA\n\n"
        "👉 Choisis un plat",
        parse_mode="Markdown",
        reply_markup=menu
    )

    context.user_data["step"] = "choix"

# =========================
# GESTION DES MESSAGES
# =========================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    step = context.user_data.get("step")

    # ----- ÉTAPE 1 : choix du plat -----
    if step == "choix":
        produits = {
            "Burger": ("Burger + frites", "3 500 FCFA"),
            "Pizza": ("Pizza", "5 000 FCFA"),
            "Riz": ("Riz poulet", "4 000 FCFA"),
        }

        for key, (produit, prix) in produits.items():
            if key in text:
                context.user_data["produit"] = produit
                context.user_data["prix"] = prix
                context.user_data["step"] = "infos"

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

        await update.message.reply_text("❌ Choisis un plat du menu.")
        return

    # ----- ÉTAPE 2 : infos client -----
    if step == "infos":
        produit = context.user_data.get("produit")
        prix = context.user_data.get("prix")
        infos = text

        # Confirmation client
        await update.message.reply_text(
            "✅ *Commande confirmée !*\n\n"
            f"🍽️ Plat : {produit}\n"
            f"💰 Prix : {prix}\n"
            f"📍 Infos : {infos}\n\n"
            "⏱️ Livraison en cours\nMerci 🙏",
            parse_mode="Markdown"
        )

        # Message admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "📦 *NOUVELLE COMMANDE*\n\n"
                f"👤 Client : @{update.effective_user.username}\n"
                f"🍽️ Plat : {produit}\n"
                f"💰 Prix : {prix}\n"
                f"📍 Infos : {infos}"
            ),
            parse_mode="Markdown"
        )

        context.user_data.clear()
        return

# =========================
# MAIN
# =========================
def main():
    if not TOKEN:
        raise RuntimeError("❌ BOT_TOKEN manquant")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(shop, pattern="shop"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    print("✅ Bot en ligne")
    app.run_polling()

if __name__ == "__main__":
    main()
