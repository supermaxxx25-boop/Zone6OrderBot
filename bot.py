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
ADMIN_ID = 8348647959  # ⚠️ remplace par TON vrai ID

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
        "🍽️ *Menu Zone 6 Food*\n\n"
        "🍔 Burger + frites – 3 500 FCFA\n"
        "🍕 Pizza – 5 000 FCFA\n"
        "🍚 Riz poulet – 4 000 FCFA\n\n"
        "👉 Choisis un plat",
        parse_mode="Markdown",
        reply_markup=menu
    )

    context.user_data["step"] = "choix_plat"

# =========================
# AFFICHAGE QUANTITÉ
# =========================
async def afficher_quantite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qte = context.user_data["quantite"]

    clavier = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➖", callback_data="moins"),
            InlineKeyboardButton(f"{qte}", callback_data="noop"),
            InlineKeyboardButton("➕", callback_data="plus"),
        ],
        [InlineKeyboardButton("✅ Valider quantité", callback_data="valider_qte")]
    ])

    await update.message.reply_text(
        "🔢 *Choisis la quantité*",
        parse_mode="Markdown",
        reply_markup=clavier
    )

# =========================
# CALLBACK BOUTONS QUANTITÉ
# =========================
async def quantite_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "quantite" not in context.user_data:
        return

    if query.data == "plus":
        context.user_data["quantite"] += 1

    elif query.data == "moins":
        if context.user_data["quantite"] > 1:
            context.user_data["quantite"] -= 1

    elif query.data == "valider_qte":
        context.user_data["step"] = "infos"

        await query.message.reply_text(
            "📍 Envoie maintenant :\n"
            "• Adresse\n"
            "• Téléphone\n\n"
            "💵 Paiement à la livraison"
        )
        return

    # Met à jour l’affichage
    qte = context.user_data["quantite"]
    clavier = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➖", callback_data="moins"),
            InlineKeyboardButton(f"{qte}", callback_data="noop"),
            InlineKeyboardButton("➕", callback_data="plus"),
        ],
        [InlineKeyboardButton("✅ Valider quantité", callback_data="valider_qte")]
    ])

    await query.message.edit_reply_markup(reply_markup=clavier)

# =========================
# MESSAGES TEXTE
# =========================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    step = context.user_data.get("step")

    # ---- CHOIX DU PLAT ----
    if step == "choix_plat":
        produits = {
            "Burger": ("Burger + frites", 3500),
            "Pizza": ("Pizza", 5000),
            "Riz": ("Riz poulet", 4000),
        }

        for key, (produit, prix) in produits.items():
            if key in text:
                context.user_data["produit"] = produit
                context.user_data["prix"] = prix
                context.user_data["quantite"] = 1
                context.user_data["step"] = "quantite"

                await afficher_quantite(update, context)
                return

        await update.message.reply_text("❌ Choisis un plat du menu.")
        return

    # ---- INFOS CLIENT ----
    if step == "infos":
        user = update.effective_user

        produit = context.user_data["produit"]
        prix = context.user_data["prix"]
        quantite = context.user_data["quantite"]
        total = prix * quantite
        infos = text

        # Client
        await update.message.reply_text(
            "✅ *Commande confirmée !*\n\n"
            f"🍽️ Plat : {produit}\n"
            f"🔢 Quantité : {quantite}\n"
            f"💰 Total : {total} FCFA\n"
            f"📍 Infos : {infos}\n\n"
            "⏱️ Livraison en cours.\nMerci 🙏",
            parse_mode="Markdown"
        )

        # Admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "📦 *NOUVELLE COMMANDE*\n\n"
                f"👤 Nom : {user.first_name or ''} {user.last_name or ''}\n"
                f"🔗 Username : @{user.username if user.username else 'Aucun'}\n"
                f"🆔 ID client : `{user.id}`\n\n"
                f"🍽️ Plat : {produit}\n"
                f"🔢 Quantité : {quantite}\n"
                f"💰 Total : {total} FCFA\n"
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
    app.add_handler(CallbackQueryHandler(quantite_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    print("✅ Bot en ligne")
    app.run_polling()

if __name__ == "__main__":
    main()
