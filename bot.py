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
# MESSAGE TEXTE
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

        # 📤 Message admin
        resume = "🆕 *NOUVELLE COMMANDE*\n\n"
        for cle, qte in panier.items():
            p = MENU[cle]
            resume += f"{p['nom']} x{qte}\n"

        resume += f"\n💰 Total : {total} €"
        resume += f"\n📍 Infos client : {infos}"
        resume += f"\n🆔 ID : `{order_id}`"

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=resume,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Accepter", callback_data=f"accept_{order_id}"),
                    InlineKeyboardButton("❌ Refuser", callback_data=f"reject_{order_id}")
                ]
            ])
        )

        context.user_data.clear()
        return

    await start(update, context)

# =====================
# BOUTIQUE / PANIER
# =====================
async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    clavier = [
        [InlineKeyboardButton(cat["nom"], callback_data=f"cat_{key}")]
        for key, cat in CATEGORIES.items()
    ]
    clavier.append([InlineKeyboardButton("🛒 Panier", callback_data="panier")])

    await q.edit_message_text(
        "🍽️ *Menu Zone6 Food*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

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
    clavier.append([InlineKeyboardButton("⬅️ Retour", callback_data="boutique")])

    await q.edit_message_text(
        categorie["nom"],
        reply_markup=InlineKeyboardMarkup(clavier)
    )

async def ajouter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    context.user_data.setdefault("panier", {})
    produit = q.data.replace("add_", "")
    panier = context.user_data["panier"]
    panier[produit] = panier.get(produit, 0) + 1

    await afficher_panier(q, context)

async def panier_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await afficher_panier(q, context)

async def afficher_panier(q, context):
    panier = context.user_data.get("panier", {})
    if not panier:
        await q.edit_message_text("🛒 Panier vide")
        return

    texte = "🛒 *Ton panier*\n\n"
    for cle, qte in panier.items():
        p = MENU[cle]
        texte += f"{p['nom']} x{qte}\n"

    total = calcul_total(panier)
    texte += f"\n💰 Total : {total} €"

    await q.edit_message_text(
        texte,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirmer", callback_data="valider")],
            [InlineKeyboardButton("⬅️ Menu", callback_data="boutique")]
        ])
    )

async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["attente_infos"] = True

    await q.edit_message_text(
        "📍 Envoie ton adresse + téléphone",
        parse_mode="Markdown"
    )

# =====================
# ADMIN : ACCEPT / REFUSE + BADGE
# =====================
async def accepter_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Commande acceptée ✅")

    order_id = q.data.replace("accept_", "")
    cmd = COMMANDES.pop(order_id, None)
    if not cmd:
        return

    await context.bot.send_message(
        chat_id=cmd["client_id"],
        text="✅ *Commande acceptée !*\nElle est en préparation 🍽️",
        parse_mode="Markdown"
    )

    nouveau_texte = q.message.text + "\n\n🟢 *STATUT : ACCEPTÉE*"
    await q.edit_message_text(
        nouveau_texte,
        parse_mode="Markdown"
    )

async def refuser_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Commande refusée ❌")

    order_id = q.data.replace("reject_", "")
    cmd = COMMANDES.pop(order_id, None)
    if not cmd:
        return

    await context.bot.send_message(
        chat_id=cmd["client_id"],
        text="❌ *Commande refusée*\nMerci de contacter Zone6 🙏",
        parse_mode="Markdown"
    )

    nouveau_texte = q.message.text + "\n\n🔴 *STATUT : REFUSÉE*"
    await q.edit_message_text(
        nouveau_texte,
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
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(boutique, "^boutique$"))
    app.add_handler(CallbackQueryHandler(afficher_categorie, "^cat_"))
    app.add_handler(CallbackQueryHandler(ajouter, "^add_"))
    app.add_handler(CallbackQueryHandler(panier_handler, "^panier$"))
    app.add_handler(CallbackQueryHandler(valider, "^valider$"))

    app.add_handler(CallbackQueryHandler(accepter_commande, "^accept_"))
    app.add_handler(CallbackQueryHandler(refuser_commande, "^reject_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Zone6 Food — Bot actif")
    app.run_polling()

if __name__ == "__main__":
    main()
