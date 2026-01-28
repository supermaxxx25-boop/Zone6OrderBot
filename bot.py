import os
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
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

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN manquant (Railway > Variables)")

COMMANDES = {}

# =====================
# CATEGORIES & PRODUITS
# =====================
CATEGORIES = {
    "burgers": {
        "nom": "🍔 Burgers",
        "produits": {
            "burger_simple": {"nom": "🍔 Burger simple + frites", "prix": 7},
            "burger_double": {"nom": "🍔 Burger double + frites", "prix": 9},
        }
    },
    "pizzas": {
        "nom": "🍕 Pizzas",
        "produits": {
            "pizza_fromage": {"nom": "🍕 Pizza fromage", "prix": 10},
            "pizza_pepperoni": {"nom": "🍕 Pizza pepperoni", "prix": 11},
        }
    },
    "plats": {
        "nom": "🍛 Plats",
        "produits": {
            "riz_poulet": {"nom": "🍛 Riz sauce poulet", "prix": 8},
        }
    }
}

MENU = {
    key: prod
    for cat in CATEGORIES.values()
    for key, prod in cat["produits"].items()
}

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salut et bienvenue dans la Zone6,\n🛒 Tu peux commander ici 👇",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍️ Ouvrir la boutique", callback_data="boutique")]
        ])
    )

# =====================
# MESSAGE TEXTE UNIQUE
# =====================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("attente_infos"):
        panier = context.user_data.get("panier", {})
        if not panier:
            return

        user = update.message.from_user
        infos = update.message.text
        total = calcul_total(panier)
        order_id = str(uuid.uuid4())[:8]

        COMMANDES[order_id] = {
            "client_id": user.id,
            "client_nom": user.full_name,
            "panier": panier.copy(),
            "total": total,
            "infos": infos
        }

        await update.message.reply_text(
            "⏳ *Commande envoyée*\nZone6 va la confirmer rapidement 🙏",
            parse_mode="Markdown"
        )

        context.user_data.clear()
        return

    await update.message.reply_text(
        "👋 Salut et bienvenue dans la Zone6,\n🛒 Tu peux commander ici 👇",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍️ Ouvrir la boutique", callback_data="boutique")]
        ])
    )

# =====================
# BOUTIQUE
# =====================
async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    clavier = [
        [InlineKeyboardButton(cat["nom"], callback_data=f"cat_{key}")]
        for key, cat in CATEGORIES.items()
    ]
    clavier.append([InlineKeyboardButton("🛒 Voir mon panier", callback_data="panier")])

    await q.edit_message_text(
        "🍽️ *Menu Zone 6 Food*\n\nChoisis une catégorie 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# PRODUITS PAR CATEGORIE
# =====================
async def afficher_categorie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    cat_key = q.data.replace("cat_", "")
    categorie = CATEGORIES.get(cat_key)
    if not categorie:
        return

    clavier = [
        [InlineKeyboardButton(prod["nom"], callback_data=f"add_{key}")]
        for key, prod in categorie["produits"].items()
    ]
    clavier.append([
        InlineKeyboardButton("⬅️ Retour catégories", callback_data="boutique"),
        InlineKeyboardButton("🛒 Panier", callback_data="panier")
    ])

    await q.edit_message_text(
        f"{categorie['nom']}\n\nSélectionne un produit 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# AJOUT PANIER
# =====================
async def ajouter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    context.user_data.setdefault("panier", {})
    produit = q.data.replace("add_", "")
    panier = context.user_data["panier"]
    panier[produit] = panier.get(produit, 0) + 1

    await afficher_panier(q, context)

# =====================
# PANIER
# =====================
async def panier_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await afficher_panier(q, context)

async def afficher_panier(q, context):
    panier = context.user_data.get("panier", {})

    if not panier:
        await q.edit_message_text(
            "🛒 *Ton panier est vide*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Retour menu", callback_data="boutique")]
            ])
        )
        return

    texte = "🛒 *Ton panier*\n\n"
    clavier = []

    for cle, qte in panier.items():
        p = MENU[cle]
        texte += (
            f"{p['nom']}\n"
            f"➜ Quantité : {qte}\n"
            f"➜ Sous-total : {p['prix'] * qte} €\n\n"
        )

        clavier.append([
            InlineKeyboardButton("➖", callback_data=f"moins_{cle}"),
            InlineKeyboardButton("➕", callback_data=f"plus_{cle}"),
            InlineKeyboardButton("🗑️ Retirer", callback_data=f"del_{cle}")
        ])

    total = calcul_total(panier)
    texte += f"💰 *Total : {total} €*"

    clavier.append([InlineKeyboardButton("✅ Confirmer la commande", callback_data="valider")])
    clavier.append([InlineKeyboardButton("⬅️ Continuer mes achats", callback_data="boutique")])

    await q.edit_message_text(
        texte,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# VALIDER
# =====================
async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    context.user_data["attente_infos"] = True

    await q.edit_message_text(
        "📍 *Merci de préciser :*\n• Adresse de livraison\n• Téléphone",
        parse_mode="Markdown"
    )

# =====================
# UTILS
# =====================
def calcul_total(panier):
    return sum(MENU[k]["prix"] * v for k, v in panier.items())

# =====================
# MAIN
# =====================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(boutique, pattern="^boutique$"))
    app.add_handler(CallbackQueryHandler(afficher_categorie, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(ajouter, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(panier_handler, pattern="^panier$"))
    app.add_handler(CallbackQueryHandler(valider, pattern="^valider$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Zone 6 Food — Bot actif")
    app.run_polling()

if __name__ == "__main__":
    main()
