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
DEVISE = "€"

MENU = {
    "burger": {"nom": "🍔 Burger + frites", "prix": 7},
    "pizza": {"nom": "🍕 Pizza", "prix": 10},
    "riz": {"nom": "🍛 Riz sauce poulet", "prix": 8},
}

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clavier = [[InlineKeyboardButton("🛒 Ouvrir la boutique", callback_data="boutique")]]
    await update.message.reply_text(
        "👋 Bienvenue chez *Zone 6 Food*\n\n"
        "Commande facilement en quelques clics 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# BOUTIQUE
# =====================
async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "panier" not in context.user_data:
        context.user_data["panier"] = {}

    clavier = [
        [
            InlineKeyboardButton("🍔 Burger", callback_data="add_burger"),
            InlineKeyboardButton("🍕 Pizza", callback_data="add_pizza")
        ],
        [
            InlineKeyboardButton("🍛 Riz poulet", callback_data="add_riz")
        ],
        [
            InlineKeyboardButton("🛒 Voir / modifier mon panier", callback_data="panier")
        ]
    ]

    await query.edit_message_text(
        "🍽️ *Menu Zone 6 Food*\n\n"
        "🍔 Burger + frites – 7 €\n"
        "🍕 Pizza – 10 €\n"
        "🍛 Riz sauce poulet – 8 €\n\n"
        "👉 Clique sur un plat pour l’ajouter au panier",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# AJOUT AU PANIER
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
# PANIER HANDLER
# =====================
async def panier_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await afficher_panier(query, context)

# =====================
# AFFICHAGE PANIER (UX)
# =====================
async def afficher_panier(query, context):
    panier = context.user_data.get("panier", {})

    if not panier:
        await query.edit_message_text(
            "🛒 *Ton panier est vide*\n\n"
            "Ajoute des plats depuis le menu 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Retour au menu", callback_data="boutique")]
            ])
        )
        return

    texte = (
        "🛒 *Ton panier*\n"
        "_Utilise ➕ ➖ pour modifier les quantités_\n"
        "_🗑️ pour retirer un plat_\n\n"
    )

    clavier = []

    for cle, qte in panier.items():
        produit = MENU[cle]
        sous_total = produit["prix"] * qte

        texte += (
            f"{produit['nom']}\n"
            f"➜ Quantité : {qte}\n"
            f"➜ Sous-total : {sous_total} {DEVISE}\n\n"
        )

        clavier.append([
            InlineKeyboardButton("➖", callback_data=f"moins_{cle}"),
            InlineKeyboardButton("➕", callback_data=f"plus_{cle}"),
            InlineKeyboardButton("🗑️ Retirer", callback_data=f"del_{cle}")
        ])

    total = calcul_total(panier)
    texte += f"💰 *Total à payer : {total} {DEVISE}*"

    clavier.append([
        InlineKeyboardButton("✅ Confirmer ma commande", callback_data="valider")
    ])
    clavier.append([
        InlineKeyboardButton("⬅️ Continuer mes achats", callback_data="boutique")
    ])

    await query.edit_message_text(
        texte,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# MODIFIER PANIER
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
# VALIDATION
# =====================
async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    panier = context.user_data.get("panier", {})
    total = calcul_total(panier)

    await query.edit_message_text(
        f"🧾 *Récapitulatif de ta commande*\n\n"
        f"{resume_panier(panier)}\n"
        f"💰 *Total : {total} {DEVISE}*\n\n"
        "📍 Envoie maintenant :\n"
        "• Adresse de livraison\n"
        "• Numéro de téléphone",
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

    # Message client (UX ++)
    await update.message.reply_text(
        "✅ *Commande confirmée !*\n\n"
        "📦 Notre équipe prépare ta commande.\n"
        "📞 Tu peux être contacté si besoin.\n\n"
        f"{resume_panier(panier)}"
        f"\n💰 *Total : {total} {DEVISE}*\n\n"
        "🙏 Merci pour ta confiance !",
        parse_mode="Markdown"
    )

    # Message admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=
        "🆕 *NOUVELLE COMMANDE*\n\n"
        f"👤 Client : {user.full_name}\n"
        f"🆔 ID : `{user.id}`\n\n"
        f"{resume_panier(panier)}"
        f"\n💰 Total : {total} {DEVISE}\n\n"
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
        texte += f"• {produit['nom']} x{qte} = {produit['prix']*qte} {DEVISE}\n"
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
    app.add_handler(CallbackQueryHandler(panier_handler, pattern="^panier$"))
    app.add_handler(CallbackQueryHandler(modifier_panier, pattern="^(plus|moins|del)_"))
    app.add_handler(CallbackQueryHandler(valider, pattern="^valider$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, infos_client))

    print("🤖 Bot Zone 6 Food prêt (UX améliorée)")
    app.run_polling()

if __name__ == "__main__":
    main()
