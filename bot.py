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
        "👋 Bienvenue dans la Zone6 👽\n🛒 Tu peux commander ici 👇",
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
        await q.edit_message_text(
            "🛒 Ton panier est vide",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Menu", callback_data="boutique")]
            ])
        )
        return

    texte = "🛒 *Ton panier*\n\n"
    for k, qte in panier.items():
        texte += f"{MENU[k]['nom']} x{qte}\n"

    texte += f"\n💰 Total : {calcul_total(panier)} {DEVISE}"

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
    await q.edit_message_text(
        "Merci de nous fournir :\n\n"
        "- Ton adresse 📍\n\n"
        "- Ton numéro 📲"
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
        username = f"@{user.username}" if user.username else "—"
        infos = update.message.text
        order_id = str(uuid.uuid4())[:8]
        total = calcul_total(panier)

        COMMANDES[order_id] = {
            "client_id": user.id,
            "panier": panier.copy()
        }

        recap = "🧾 *Récap de ta commande*\n\n"
        for k, qte in panier.items():
            recap += f"{MENU[k]['nom']} x{qte}\n"

        recap += f"\n💰 Total : {total} {DEVISE}"
        recap += f"\n🆔 Commande : `{order_id}`"
        recap += "\n\n⏳ *STATUT : EN ATTENTE DE VALIDATION*"

        msg_client = await update.message.reply_text(
            recap,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Annuler la commande", callback_data=f"cancel_{order_id}")]
            ])
        )

        COMMANDES[order_id]["message_id"] = msg_client.message_id

        texte_admin = (
            "🆕 *NOUVELLE COMMANDE*\n\n"
            f"👤 Client : {user.full_name}\n"
            f"🔗 {username}\n\n"
        )

        for k, qte in panier.items():
            texte_admin += f"{MENU[k]['nom']} x{qte}\n"

        texte_admin += f"\n💰 Total : {total} {DEVISE}"
        texte_admin += f"\n📍 Infos : {infos}"
        texte_admin += f"\n🆔 `{order_id}`"

        msg_admin = await context.bot.send_message(
            ADMIN_ID,
            texte_admin,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Accepter", callback_data=f"accept_{order_id}"),
                    InlineKeyboardButton("❌ Refuser", callback_data=f"reject_{order_id}")
                ]
            ])
        )

        COMMANDES[order_id]["admin_message_id"] = msg_admin.message_id
        context.user_data.clear()
        return

    await start(update, context)

# =====================
# ANNULATION CLIENT
# =====================
async def annuler_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("cancel_", "")
    if oid not in COMMANDES:
        return

    commande = COMMANDES.pop(oid)

    await q.edit_message_text("❌ *Commande annulée*", parse_mode="Markdown")

    try:
        await context.bot.edit_message_reply_markup(
            chat_id=ADMIN_ID,
            message_id=commande["admin_message_id"],
            reply_markup=None
        )
    except:
        pass

# =====================
# STATUTS ADMIN
# =====================
async def accepter_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    oid = q.data.replace("accept_", "")
    if oid not in COMMANDES:
        return

    await q.edit_message_text(q.message.text + "\n\n🟢 *COMMANDE ACCEPTÉE*", parse_mode="Markdown")

async def refuser_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    oid = q.data.replace("reject_", "")
    if oid not in COMMANDES:
        return

    COMMANDES.pop(oid)
    await q.edit_message_text(q.message.text + "\n\n🔴 *COMMANDE REFUSÉE*", parse_mode="Markdown")

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
    app.add_handler(CallbackQueryHandler(annuler_commande, "^cancel_"))
    app.add_handler(CallbackQueryHandler(accepter_commande, "^accept_"))
    app.add_handler(CallbackQueryHandler(refuser_commande, "^reject_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Zone6 Food — Bot actif")
    app.run_polling()

if __name__ == "__main__":
    main()
