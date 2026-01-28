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
ADMIN_ID = 8348647959  # ⚠️ ton ID

PRODUITS = {
    "Burger": ("🍔 Burger + frites", 3500),
    "Pizza": ("🍕 Pizza", 5000),
    "Riz": ("🍚 Riz poulet", 4000),
}

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["panier"] = {}

    clavier = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Boutique", callback_data="shop")],
        [InlineKeyboardButton("🧺 Voir panier", callback_data="panier")]
    ])

    await update.message.reply_text(
        "👋 Bienvenue sur *Zone 6 Food* 🍽️\n\n"
        "Ajoute des plats puis gère ton panier 👇",
        parse_mode="Markdown",
        reply_markup=clavier
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
        "🍽️ *Menu*\nClique sur un plat pour l’ajouter 👇",
        parse_mode="Markdown",
        reply_markup=menu
    )

# =========================
# AJOUT AU PANIER
# =========================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    panier = context.user_data.setdefault("panier", {})

    if "panier" in text.lower():
        await afficher_panier(update, context)
        return

    for key in PRODUITS:
        if key in text:
            panier[key] = panier.get(key, 0) + 1
            await update.message.reply_text(
                f"✅ {PRODUITS[key][0]} ajouté\n"
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
    boutons = []
    total = 0

    for key, qte in panier.items():
        nom, prix = PRODUITS[key]
        sous_total = qte * prix
        total += sous_total

        texte += f"{nom}\n🔢 {qte} × {prix} = {sous_total} FCFA\n\n"

        boutons.append([
            InlineKeyboardButton("➖", callback_data=f"moins:{key}"),
            InlineKeyboardButton(f"{qte}", callback_data="noop"),
            InlineKeyboardButton("➕", callback_data=f"plus:{key}"),
            InlineKeyboardButton("❌", callback_data=f"del:{key}")
        ])

    texte += f"💰 *Total : {total} FCFA*"

    boutons.append([InlineKeyboardButton("✅ Valider la commande", callback_data="valider")])
    boutons.append([InlineKeyboardButton("🛒 Continuer achats", callback_data="shop")])

    await update.message.reply_text(
        texte,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(boutons)
    )

# =========================
# BOUTONS PANIER (CRITIQUE)
# =========================
async def panier_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    panier = context.user_data.get("panier", {})
    data = query.data

    if data.startswith("plus:"):
        key = data.split(":")[1]
        panier[key] += 1

    elif data.startswith("moins:"):
        key = data.split(":")[1]
        if panier[key] > 1:
            panier[key] -= 1

    elif data.startswith("del:"):
        key = data.split(":")[1]
        panier.pop(key, None)

    elif data == "valider":
        context.user_data["step"] = "infos"
        await query.message.reply_text(
            "📍 Envoie maintenant :\n• Adresse\n• Téléphone\n\n💵 Paiement à la livraison"
        )
        return

    await afficher_panier(query.message, context)

# =========================
# INFOS CLIENT
# =========================
async def infos_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") != "infos":
        return

    panier = context.user_data.get("panier", {})
    user = update.effective_user
    infos = update.message.text

    texte = ""
    total = 0

    for key, qte in panier.items():
        nom, prix = PRODUITS[key]
        sous = qte * prix
        total += sous
        texte += f"{nom} × {qte} = {sous} FCFA\n"

    await update.message.reply_text(
        f"✅ *Commande confirmée !*\n\n{texte}\n💰 Total : {total} FCFA\n📍 {infos}",
        parse_mode="Markdown"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"📦 NOUVELLE COMMANDE\n\n"
            f"Client : {user.first_name}\n"
            f"ID : {user.id}\n\n"
            f"{texte}\n"
            f"Total : {total} FCFA\n"
            f"Infos : {infos}"
        )
    )

    context.user_data.clear()

# =========================
# MAIN (ORDRE CRUCIAL)
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # ⚠️ CALLBACKS D’ABORD
    app.add_handler(CallbackQueryHandler(shop, pattern="^shop$"))
    app.add_handler(CallbackQueryHandler(afficher_panier, pattern="^panier$"))
    app.add_handler(CallbackQueryHandler(panier_buttons))

    # COMMANDES & MESSAGES APRÈS
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, infos_client))

    print("✅ Bot en ligne")
    app.run_polling()

if __name__ == "__main__":
    main()
