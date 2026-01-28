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
ADMIN_ID = 8348647959  # ⚠️ ton ID Telegram

PRODUITS = {
    "Burger": ("🍔 Burger + frites", 3500),
    "Pizza": ("🍕 Pizza", 5000),
    "Riz": ("🍚 Riz poulet", 4000),
}

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Ouvrir la boutique", callback_data="shop")],
        [InlineKeyboardButton("🧺 Voir le panier", callback_data="voir_panier")]
    ])

    context.user_data["panier"] = {}

    await update.message.reply_text(
        "👋 Bienvenue sur *Zone 6 Food* 🍽️\n\n"
        "Commande autant de plats que tu veux 👇",
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
        [["🍔 Burger", "🍕 Pizza"], ["🍚 Riz poulet"], ["🧺 Voir panier"]],
        resize_keyboard=True
    )

    await query.message.reply_text(
        "🍽️ *Menu*\n\n"
        "🍔 Burger + frites – 3 500 FCFA\n"
        "🍕 Pizza – 5 000 FCFA\n"
        "🍚 Riz poulet – 4 000 FCFA\n\n"
        "👉 Clique pour ajouter au panier",
        parse_mode="Markdown",
        reply_markup=menu
    )

# =========================
# AJOUT AU PANIER
# =========================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    panier = context.user_data.setdefault("panier", {})

    # Voir panier
    if "panier" in text.lower():
        await afficher_panier(update, context)
        return

    for key, (nom, prix) in PRODUITS.items():
        if key in text:
            panier[key] = panier.get(key, 0) + 1
            await update.message.reply_text(
                f"✅ {nom} ajouté au panier\n"
                f"🔢 Quantité : {panier[key]}"
            )
            return

# =========================
# AFFICHER PANIER
# =========================
async def afficher_panier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    panier = context.user_data.get("panier", {})

    if not panier:
        await update.message.reply_text("🧺 Ton panier est vide.")
        return

    texte = "🧺 *Ton panier :*\n\n"
    total = 0

    for key, qte in panier.items():
        nom, prix = PRODUITS[key]
        sous_total = prix * qte
        total += sous_total
        texte += f"{nom}\n🔢 {qte} × {prix} = {sous_total} FCFA\n\n"

    texte += f"💰 *Total : {total} FCFA*"

    clavier = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Valider la commande", callback_data="valider")],
        [InlineKeyboardButton("➕ Continuer les achats", callback_data="shop")]
    ])

    await update.message.reply_text(
        texte,
        parse_mode="Markdown",
        reply_markup=clavier
    )

# =========================
# VALIDATION PANIER
# =========================
async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["step"] = "infos"

    await query.message.reply_text(
        "📍 Envoie maintenant :\n"
        "• Adresse\n"
        "• Téléphone\n\n"
        "💵 Paiement à la livraison"
    )

# =========================
# INFOS CLIENT & CONFIRMATION
# =========================
async def infos_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") != "infos":
        return

    panier = context.user_data.get("panier", {})
    user = update.effective_user
    infos = update.message.text

    texte_panier = ""
    total = 0

    for key, qte in panier.items():
        nom, prix = PRODUITS[key]
        sous_total = prix * qte
        total += sous_total
        texte_panier += f"{nom} × {qte} = {sous_total} FCFA\n"

    # Client
    await update.message.reply_text(
        "✅ *Commande confirmée !*\n\n"
        f"{texte_panier}\n"
        f"💰 Total : {total} FCFA\n"
        f"📍 Infos : {infos}\n\n"
        "⏱️ Livraison en cours. Merci 🙏",
        parse_mode="Markdown"
    )

    # Admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📦 *NOUVELLE COMMANDE*\n\n"
            f"👤 Client : {user.first_name or ''}\n"
            f"🆔 ID : `{user.id}`\n\n"
            f"{texte_panier}\n"
            f"💰 Total : {total} FCFA\n"
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
        raise RuntimeError("❌ BOT_TOKEN manquant")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(shop, pattern="shop"))
    app.add_handler(CallbackQueryHandler(valider, pattern="valider"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, infos_client))

    print("✅ Bot en ligne")
    app.run_polling()

if __name__ == "__main__":
    main()
