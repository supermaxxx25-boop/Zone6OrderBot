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

        # 🔴 ICI : nom + username UNIQUEMENT CÔTÉ ADMIN
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

        COMMANDES[order_id] = {
            "client_id": user.id,
            "panier": panier.copy(),
            "message_id": msg_client.message_id,
            "admin_message_id": msg_admin.message_id
        }

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
    commande = COMMANDES.get(oid)

    if not commande:
        await q.edit_message_text("⚠️ Cette commande ne peut plus être annulée.")
        return

    await q.edit_message_text(
        "❌ *Commande annulée avec succès*",
        parse_mode="Markdown"
    )

    try:
        await context.bot.edit_message_text(
            chat_id=ADMIN_ID,
            message_id=commande["admin_message_id"],
            text=q.message.text + "\n\n❌ *COMMANDE ANNULÉE PAR LE CLIENT*",
            parse_mode="Markdown"
        )
    except:
        pass

    COMMANDES.pop(oid, None)

# =====================
# ADMIN ACTIONS
# =====================
async def accepter_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("accept_", "")
    commande = COMMANDES.get(oid)
    if not commande:
        return

    await update_recap_client(context, oid, "🟢 *COMMANDE ACCEPTÉE*")
    await q.edit_message_reply_markup(reply_markup=None)

async def refuser_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    oid = q.data.replace("reject_", "")
    commande = COMMANDES.get(oid)
    if not commande:
        return

    await update_recap_client(context, oid, "🔴 *COMMANDE REFUSÉE*")
    await q.edit_message_reply_markup(reply_markup=None)
    COMMANDES.pop(oid)

# =====================
# UTILS
# =====================
async def update_recap_client(context, oid, statut):
    commande = COMMANDES.get(oid)
    if not commande:
        return

    texte = "🧾 *Récap de ta commande*\n\n"
    for k, qte in commande["panier"].items():
        texte += f"{MENU[k]['nom']} x{qte}\n"

    texte += f"\n💰 Total : {calcul_total(commande['panier'])} {DEVISE}"
    texte += f"\n🆔 Commande : `{oid}`"
    texte += f"\n\n{statut}"

    await context.bot.edit_message_text(
        chat_id=commande["client_id"],
        message_id=commande["message_id"],
        text=texte,
        parse_mode="Markdown"
    )

def calcul_total(panier):
    return sum(MENU[k]["prix"] * q for k, q in panier.items())

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(boutique, "^boutique$"))
    app.add_handler(CallbackQueryHandler(annuler_commande, "^cancel_"))
    app.add_handler(CallbackQueryHandler(accepter_commande, "^accept_"))
    app.add_handler(CallbackQueryHandler(refuser_commande, "^reject_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Zone6 Food — Bot actif")
    app.run_polling()

if __name__ == "__main__":
    main()
