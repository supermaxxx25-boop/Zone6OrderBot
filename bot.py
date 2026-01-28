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
# MENU
# =====================
CATEGORIES = {
    "burgers": {
        "nom": "🍔 Burgers",
        "produits": {
            "burger_simple": {"nom": "Burger simple + frites", "prix": 7},
            "burger_double": {"nom": "Burger double + frites", "prix": 9},
        }
    },
    "pizzas": {
        "nom": "🍕 Pizzas",
        "produits": {
            "pizza_fromage": {"nom": "Pizza fromage", "prix": 10},
            "pizza_pepperoni": {"nom": "Pizza pepperoni", "prix": 11},
        }
    }
}

MENU = {k: v for c in CATEGORIES.values() for k, v in c["produits"].items()}

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenue chez *Zone6 Food* 🍽️",
        parse_mode="Markdown",
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
        order_id = str(uuid.uuid4())[:8]
        total = calcul_total(panier)

        COMMANDES[order_id] = {
            "client_id": user.id,
            "panier": panier.copy()
        }

        await update.message.reply_text(
            "⏳ *Commande envoyée*\nEn attente de validation",
            parse_mode="Markdown"
        )

        texte = "🆕 *NOUVELLE COMMANDE*\n\n"
        for k, qte in panier.items():
            texte += f"{MENU[k]['nom']} x{qte}\n"

        texte += f"\n💰 Total : {total} €"
        texte += f"\n📍 Infos : {infos}"
        texte += f"\n🆔 `{order_id}`"

        await context.bot.send_message(
            ADMIN_ID,
            texte,
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
# BOUTIQUE
# =====================
async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.edit_message_text(
        "🍽️ *Menu*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🍔 Burgers", callback_data="cat_burgers")],
            [InlineKeyboardButton("🍕 Pizzas", callback_data="cat_pizzas")],
            [InlineKeyboardButton("🛒 Panier", callback_data="panier")]
        ])
    )

async def afficher_categorie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    cat = q.data.replace("cat_", "")
    boutons = [
        [InlineKeyboardButton(p["nom"], callback_data=f"add_{k}")]
        for k, p in CATEGORIES[cat]["produits"].items()
    ]
    boutons.append([InlineKeyboardButton("⬅️ Retour", callback_data="boutique")])

    await q.edit_message_text(
        CATEGORIES[cat]["nom"],
        reply_markup=InlineKeyboardMarkup(boutons)
    )

async def ajouter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    context.user_data.setdefault("panier", {})
    key = q.data.replace("add_", "")
    context.user_data["panier"][key] = context.user_data["panier"].get(key, 0) + 1
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
    for k, qte in panier.items():
        texte += f"{MENU[k]['nom']} x{qte}\n"

    texte += f"\n💰 Total : {calcul_total(panier)} €"

    await q.edit_message_text(
        texte,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Commander", callback_data="valider")],
            [InlineKeyboardButton("⬅️ Menu", callback_data="boutique")]
        ])
    )

async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["attente_infos"] = True
    await q.edit_message_text("📍 Envoie adresse + téléphone")

# =====================
# STATUTS ADMIN
# =====================
async def accepter_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("accept_", "")
    await context.bot.send_message(COMMANDES[oid]["client_id"],
        "🟢 *Commande acceptée*",
        parse_mode="Markdown"
    )

    await q.edit_message_text(
        q.message.text + "\n\n🟢 *STATUT : ACCEPTÉE*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏳ En préparation", callback_data=f"prep_{oid}")]
        ])
    )

async def preparation_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("prep_", "")
    await context.bot.send_message(COMMANDES[oid]["client_id"],
        "⏳ *Commande en préparation*",
        parse_mode="Markdown"
    )

    await q.edit_message_text(
        q.message.text + "\n\n⏳ *STATUT : EN PRÉPARATION*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏎️ En livraison", callback_data=f"livraison_{oid}")]
        ])
    )

async def livraison_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("livraison_", "")
    await context.bot.send_message(COMMANDES[oid]["client_id"],
        "🏎️ *Votre commande arrive !*",
        parse_mode="Markdown"
    )

    await q.edit_message_text(
        q.message.text + "\n\n🏎️ *STATUT : EN LIVRAISON*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Commande livrée", callback_data=f"livree_{oid}")]
        ])
    )

async def livree_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("livree_", "")
    await context.bot.send_message(COMMANDES[oid]["client_id"],
        "✅ *Commande livrée ! Merci ❤️*",
        parse_mode="Markdown"
    )

    COMMANDES.pop(oid, None)

    await q.edit_message_text(
        q.message.text + "\n\n✅ *STATUT : LIVRÉE*",
        parse_mode="Markdown"
    )

async def refuser_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("reject_", "")
    await context.bot.send_message(COMMANDES[oid]["client_id"],
        "❌ *Commande refusée*",
        parse_mode="Markdown"
    )

    COMMANDES.pop(oid, None)

    await q.edit_message_text(
        q.message.text + "\n\n🔴 *STATUT : REFUSÉE*",
        parse_mode="Markdown"
    )

# =====================
# UTILS
# =====================
def calcul_total(panier):
    return sum(MENU[k]["prix"] * q for k, q in panier.items())

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
    app.add_handler(CallbackQueryHandler(preparation_commande, "^prep_"))
    app.add_handler(CallbackQueryHandler(livraison_commande, "^livraison_"))
    app.add_handler(CallbackQueryHandler(livree_commande, "^livree_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Zone6 Food — Bot actif")
    app.run_polling()

if __name__ == "__main__":
    main()
