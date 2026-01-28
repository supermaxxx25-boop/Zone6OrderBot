import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8348647959

MENU = {
    "burger": {"nom": "🍔 Burger + frites", "prix": 7},
    "pizza": {"nom": "🍕 Pizza", "prix": 10},
    "riz": {"nom": "🍛 Riz sauce poulet", "prix": 8},
}

DEVISE = "€"

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clavier = [[InlineKeyboardButton("🛒 Ouvrir la boutique", callback_data="boutique")]]
    await update.message.reply_text(
        "👋 Bienvenue chez *Zone 6 Food*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# BOUTIQUE
# =====================
async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["panier"] = {}

    await afficher_boutique(query, context)

async def afficher_boutique(query, context):
    clavier = [
        [
            InlineKeyboardButton("🍔 Burger", callback_data="add_burger"),
            InlineKeyboardButton("🍕 Pizza", callback_data="add_pizza"),
        ],
        [
            InlineKeyboardButton("🍛 Riz poulet", callback_data="add_riz")
        ],
        [
            InlineKeyboardButton("🛒 Voir / modifier le panier", callback_data="panier")
        ]
    ]

    await query.edit_message_text(
        "🍽️ *Menu Zone 6 Food*\n\n"
        "🍔 Burger + frites – 7 €\n"
        "🍕 Pizza – 10 €\n"
        "🍛 Riz sauce poulet – 8 €\n\n"
        "👉 Clique pour ajouter au panier",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# AJOUT PANIER
# =====================
async def ajouter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    produit = query.data.replace("add_", "")
    panier = context.user_data.get("panier", {})
    panier[produit] = panier.get(produit, 0) + 1
    context.user_data["panier"] = panier

    await afficher_panier(query, context)

# =====================
# PANIER
# =====================
async def afficher_panier(query, context):
    panier = context.user_data.get("panier", {})

    if not panier:
        await query.edit_message_text("🛒 Panier vide")
        return

    texte = "🛒 *Ton panier*\n\n"
    clavier = []

    for cle, qte in panier.items():
        produit = MENU[cle]
        texte += f"{produit['nom']} x{qte} = {produit['prix']*qte} {DEVISE}\n"

        clavier.append([
            InlineKeyboardButton("➖", callback_data=f"moins_{cle}"),
            InlineKeyboardButton("➕", callback_data=f"plus_{cle}"),
            InlineKeyboardButton("❌", callback_data=f"del_{cle}")
        ])

    total = calcul_total(panier)
    texte += f"\n💰 *Total : {total} {DEVISE}*"

    clavier.append([
        InlineKeyboardButton("✅ Valider la commande", callback_data="valider"),
        InlineKeyboardButton("⬅️ Retour menu", callback_data="boutique")
    ])

    await query.edit_message_text(
        texte,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# MODIFIER QUANTITÉS
# =====================
async def modifier_panier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, produit = query.data.split("_")
    panier = context.user_data.get("panier", {})

    if produit not in panier:
        return

    if action == "plus":
        panier[produit] += 1
    elif action == "moins":
        panier[produit] -= 1
        if panier[produit] <= 0:
            del panier[produit]
    elif action == "del":
        del panier[produit]

    context.user_data["panier"] = panier
    await afficher_panier(query, context)

# =====================
# VALIDER
# =====================
async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    panier = context.user_data.get("panier", {})
    if not panier:
        await query.edit_message_text("❌ Panier vide")
        return

    total = calcul_total(panier)

    await query.edit_message_text(
        f"🧾 *Récapitulatif*\n\n"
        f"{resume_panier(panier)}\n"
        f"💰 Total : {total} {DEVISE}\n\n"
        "📍 Envoie maintenant :\n"
        "• Adresse\n"
        "• Téléphone",
        parse_mode="Markdown"
    )

    context.user_data["attente_infos"] = True

# =====================
# INFOS CLIENT
# =====================
async def infos_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("attente_infos"):
        return

    panier = context.user_data["panier"]
    infos = update.message.text
    user = update.message.from_user
    total = calcul_total(panier)

    await update.message.reply_text(
        "✅ *Commande confirmée !*\n\n"
        f"{resume_panier(panier)}\n"
        f"💰 Total : {total} {DEVISE}\n\n"
        "⏱️ Livraison en cours. Merci 🙏",
        parse_mode="Markdown"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=
        "🆕 *NOUVELLE COMMANDE*\n\n"
        f"👤 Client : {user.full_name}\n"
        f"🆔 ID : `{user.id}`\n\n"
        f"{resume_panier(panier)}\n"
        f"💰 Total : {total} {DEVISE}\n\n"
        f"📍 Infos client :\n{infos}",
        parse_mode="Markdown"
    )

    context.user_data.clear()

# =====================
# UTILS
# =====================
def resume_panier(panier):
    texte = ""
    for cle, qte in panier.items():
        produit = MENU[cle]
        texte += f"{produit['nom']} x{qte} = {produit['prix']*qte} {DEVISE}\n"
    return texte

def calcul_total(panier):
    return sum(MENU[k]["prix"] * v for k, v in panier.items())

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(boutique, pattern="^boutique$"))
    app.add_handler(CallbackQueryHandler(ajouter, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(afficher_panier, pattern="^panier$"))
    app.add_handler(CallbackQueryHandler(modifier_panier, pattern="^(plus|moins|del)_"))
    app.add_handler(CallbackQueryHandler(valider, pattern="^valider$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, infos_client))

    print("🤖 Bot Zone 6 Food prêt")
    app.run_polling()

if __name__ == "__main__":
    main()
