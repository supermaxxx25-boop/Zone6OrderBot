import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from config import BOT_TOKEN, ADMIN_ID, WEBAPP_URL

# -------- UTIL --------
def load_orders():
    with open("orders.json", "r") as f:
        return json.load(f)

def save_orders(data):
    with open("orders.json", "w") as f:
        json.dump(data, f, indent=2)

# -------- COMMANDES --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(
            "🛒 Ouvrir la boutique",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ]
    await update.message.reply_text(
        "👋 Bienvenue dans **LA ZONE6 🌿**\n\n"
        "🛍️ Clique ci-dessous pour accéder à la boutique",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# -------- RÉCEPTION COMMANDE (SIMULÉE) --------
# Cette fonction sera appelée quand tu relieras la mini-app au bot
async def new_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    order_id = len(load_orders()) + 1

    order = {
        "id": order_id,
        "user_id": user.id,
        "username": user.username,
        "items": update.message.text,
        "status": "pending"
    }

    orders = load_orders()
    orders.append(order)
    save_orders(orders)

    keyboard = [
        [
            InlineKeyboardButton("✅ Accepter", callback_data=f"accept_{order_id}"),
            InlineKeyboardButton("❌ Refuser", callback_data=f"reject_{order_id}")
        ]
    ]

    await context.bot.send_message(
        ADMIN_ID,
        f"🛎️ **Nouvelle commande #{order_id}**\n"
        f"👤 @{user.username}\n\n"
        f"{order['items']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "✅ Commande envoyée !\n"
        "⏳ En attente de validation admin."
    )

# -------- ACTIONS ADMIN --------
async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, order_id = query.data.split("_")
    order_id = int(order_id)

    orders = load_orders()
    order = next(o for o in orders if o["id"] == order_id)

    if action == "accept":
        order["status"] = "accepted"
        msg = "✅ **Commande acceptée**\n⏳ En préparation"
    else:
        order["status"] = "rejected"
        msg = "❌ **Commande refusée**"

    save_orders(orders)

    await context.bot.send_message(
        order["user_id"],
        msg,
        parse_mode="Markdown"
    )

    await query.edit_message_text(
        f"{msg}\n\n📦 Commande #{order_id}"
    )

# -------- MAIN --------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("commande", new_order))
    app.add_handler(CallbackQueryHandler(handle_admin_action))

    print("✅ Bot LA ZONE6 lancé")
    app.run_polling()

if __name__ == "__main__":
    main()
