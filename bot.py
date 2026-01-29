import os
import uuid
import json
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
COMMANDES_FILE = "commandes.json"

# =====================
# PERSISTENCE
# =====================
def save_commandes():
    with open(COMMANDES_FILE, "w") as f:
        json.dump(COMMANDES, f)

def load_commandes():
    global COMMANDES
    if os.path.exists(COMMANDES_FILE):
        with open(COMMANDES_FILE, "r") as f:
            COMMANDES = json.load(f)

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
        save_commandes()

        recap = "🧾 *Récap de ta commande*\n\n"
        for k, qte in panier.items():
            recap += f"{MENU[k]['nom']} x{qte}\n"

        recap += f"\n💰 Total : {total} {DEVISE}"
        recap += f"\n🆔 Commande : `{order_id}`"
        recap += "\n\n⏳ *STATUT : EN ATTENTE DE VALIDATION*"

        msg = await update.message.reply_text(
            recap,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Annuler la commande", callback_data=f"cancel_{order_id}")]
            ])
        )

        COMMANDES[order_id]["message_id"] = msg.message_id
        save_commandes()

        texte = (
            "🆕 *NOUVELLE COMMANDE*\n\n"
            f"👤 Client : {user.full_name}\n"
            f"🔗 {username}\n\n"
        )

        for k, qte in panier.items():
            texte += f"{MENU[k]['nom']} x{qte}\n"

        texte += f"\n💰 Total : {total} {DEVISE}"
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
# ANNULATION CLIENT
# =====================
async def annuler_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("cancel_", "")

    if oid not in COMMANDES:
        await q.edit_message_text("⚠️ Cette commande ne peut plus être annulée.")
        return

    COMMANDES.pop(oid)
    save_commandes()

    await q.edit_message_text(
        "❌ *Commande annulée avec succès*",
        parse_mode="Markdown"
    )

    await context.bot.send_message(
        ADMIN_ID,
        f"❌ *Commande annulée par le client*\n🆔 `{oid}`",
        parse_mode="Markdown"
    )

# =====================
# UTILS
# =====================
async def maj_recap_client(context, oid, statut):
    commande = COMMANDES.get(oid)
    if not commande:
        return

    panier = commande["panier"]

    texte = "🧾 *Récap de ta commande*\n\n"
    for k, qte in panier.items():
        texte += f"{MENU[k]['nom']} x{qte}\n"

    texte += f"\n💰 Total : {calcul_total(panier)} {DEVISE}"
    texte += f"\n🆔 Commande : `{oid}`"
    texte += f"\n\n{statut}"

    try:
        await context.bot.edit_message_text(
            chat_id=commande["client_id"],
            message_id=commande["message_id"],
            text=texte,
            parse_mode="Markdown"
        )
    except:
        pass

def calcul_total(panier):
    return sum(MENU[k]["prix"] * q for k, q in panier.items())

# =====================
# STATUTS ADMIN
# =====================
async def accepter_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("accept_", "")
    if oid not in COMMANDES:
        return

    await maj_recap_client(context, oid, "🟢 *COMMANDE ACCEPTÉE*")
    save_commandes()

    await q.edit_message_text(
        q.message.text + "\n\n🟢 *COMMANDE ACCEPTÉE*",
        parse_mode="Markdown"
    )

async def refuser_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("reject_", "")
    await maj_recap_client(context, oid, "❌ *COMMANDE REFUSÉE*")

    COMMANDES.pop(oid, None)
    save_commandes()

    await q.edit_message_text(
        q.message.text + "\n\n🔴 *COMMANDE REFUSÉE*",
        parse_mode="Markdown"
    )

# =====================
# MAIN
# =====================
def main():
    load_commandes()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(annuler_commande, "^cancel_"))
    app.add_handler(CallbackQueryHandler(accepter_commande, "^accept_"))
    app.add_handler(CallbackQueryHandler(refuser_commande, "^reject_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Zone6 Food — Bot actif")
    app.run_polling()

if __name__ == "__main__":
    main()
