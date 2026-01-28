import os
import uuid
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

COMMANDES = {}

# =====================
# CATEGORIES & MENU
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

# MENU global (utilisé par panier / admin)
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
# MESSAGE PAR DEFAUT
# =====================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ne répond que si on n'attend PAS les infos client
    if context.user_data.get("attente_infos"):
        return

    await update.message.reply_text(
        "👋 Salut et bienvenue dans la Zone6,\n🛒 Tu peux commander ici 👇",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍️ Ouvrir la boutique", callback_data="boutique")]
        ])
    )

# =====================
# BOUTIQUE (CATEGORIES)
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
# AJOUT AU PANIER
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
        texte += f"{p['nom']}\n➜ Quantité : {qte}\n➜ Sous-total : {p['prix'] * qte} €\n\n"

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
# MODIFIER PANIER
# =====================
async def modifier_panier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    action, cle = q.data.split("_")
    panier = context.user_data["panier"]

    if action == "plus":
        panier[cle] += 1
    elif action == "moins":
        panier[cle] -= 1
        if panier[cle] <= 0:
            del panier[cle]
    elif action == "del":
        del panier[cle]

    await afficher_panier(q, context)

# =====================
# VALIDER COMMANDE
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
# INFOS CLIENT
# =====================
async def infos_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("attente_infos"):
        return

    user = update.message.from_user
    panier = context.user_data["panier"]
    total = calcul_total(panier)
    infos = update.message.text
    order_id = str(uuid.uuid4())[:8]

    COMMANDES[order_id] = {
        "client_id": user.id,
        "client_nom": user.full_name,
        "client_username": user.username,
        "panier": panier.copy(),
        "total": total,
        "statut": "en_attente"
    }

    await update.message.reply_text(
        "⏳ *Commande envoyée*\n\nZone6 doit confirmer la commande 🙏",
        parse_mode="Markdown"
    )

    pseudo = f"@{user.username}" if user.username else "Non défini"

    await context.bot.send_message(
        ADMIN_ID,
        f"🆕 *NOUVELLE COMMANDE*\n"
        f"🆔 `{order_id}`\n\n"
        f"👤 Client : {user.full_name}\n"
        f"🔗 {pseudo}\n\n"
        f"{resume_panier(panier)}"
        f"💰 *Total : {total} €*\n\n"
        f"📍 Infos client :\n{infos}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Accepter", callback_data=f"admin_accept_{order_id}"),
                InlineKeyboardButton("❌ Refuser", callback_data=f"admin_refuse_{order_id}")
            ]
        ])
    )

    context.user_data.clear()

# =====================
# ADMIN ACTIONS
# =====================
async def admin_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    order_id = q.data.replace("admin_accept_", "")
    cmd = COMMANDES.get(order_id)
    if not cmd:
        return

    cmd["statut"] = "confirmee"

    await context.bot.send_message(
        cmd["client_id"],
        "✅ *Ta commande est acceptée !*",
        parse_mode="Markdown"
    )

    await q.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👨‍🍳 Préparation", callback_data=f"statut_prep_{order_id}"),
                InlineKeyboardButton("🛵 Livraison", callback_data=f"statut_livraison_{order_id}")
            ],
            [InlineKeyboardButton("✅ Livrée", callback_data=f"statut_livree_{order_id}")]
        ])
    )

async def admin_refuse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    order_id = q.data.replace("admin_refuse_", "")
    cmd = COMMANDES.get(order_id)
    if not cmd:
        return

    await context.bot.send_message(
        cmd["client_id"],
        "❌ *Commande refusée.*",
        parse_mode="Markdown"
    )

    del COMMANDES[order_id]
    await q.edit_message_reply_markup(reply_markup=None)

# =====================
# STATUT COMMANDE
# =====================
async def statut_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, statut, order_id = q.data.split("_")
    cmd = COMMANDES.get(order_id)
    if not cmd:
        return

    messages = {
        "prep": "👨‍🍳 *Commande en préparation*",
        "livraison": "🛵 *Commande en livraison*",
        "livree": "🎉 *Commande livrée — bon appétit !*"
    }

    await context.bot.send_message(
        cmd["client_id"],
        messages[statut],
        parse_mode="Markdown"
    )

    cmd["statut"] = statut

# =====================
# UTILS
# =====================
def calcul_total(panier):
    return sum(MENU[k]["prix"] * v for k, v in panier.items())

def resume_panier(panier):
    texte = "🧾 *Commande*\n"
    for k, v in panier.items():
        p = MENU[k]
        texte += f"• {p['nom']} x{v} = {p['prix'] * v} €\n"
    return texte + "\n"

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(boutique, "^boutique$"))
    app.add_handler(CallbackQueryHandler(afficher_categorie, "^cat_"))
    app.add_handler(CallbackQueryHandler(ajouter, "^add_"))
    app.add_handler(CallbackQueryHandler(panier_handler, "^panier$"))
    app.add_handler(CallbackQueryHandler(modifier_panier, "^(plus|moins|del)_"))
    app.add_handler(CallbackQueryHandler(valider, "^valider$"))
    app.add_handler(CallbackQueryHandler(statut_handler, "^statut_"))
    app.add_handler(CallbackQueryHandler(admin_accept, "^admin_accept_"))
    app.add_handler(CallbackQueryHandler(admin_refuse, "^admin_refuse_"))

    # ORDRE IMPORTANT
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, infos_client))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Zone 6 Food — Bot actif")
    app.run_polling()

if __name__ == "__main__":
    main()
