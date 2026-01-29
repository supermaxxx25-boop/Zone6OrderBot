import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler, ContextTypes, filters
)
from config import BOT_TOKEN, ADMIN_ID, WEBAPP_URL

def load_orders():
    with open("orders.json") as f:
        return json.load(f)

def save_orders(data):
    with open("orders.json", "w") as f:
        json.dump(data, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(
        "🛒 Ouvrir la boutique",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )]]
    await update.message.reply_text(
        "👋 Bienvenue dans **LA ZONE6 🌿**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def receive_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = json.loads(update.message.web_app_data.data)
    user = update.message.from_user

    orders = load_orders()
    order_id = len(orders) + 1

    order = {
        "id": order_id,
        "user_id": user.id,
        "username": user.username,
        "items": data["items"],
        "total": data["total"],
        "status": "pending"
    }

    orders.append(order)
    save_orders(orders)

    items_text = "\n".join(f"- {i['name']} ({i['price']}€)" for i in data["items"])

    keyboard = [[
        InlineKeyboardButton("✅ Accepter", callback_data=f"accept_{order_id}"),
        InlineKeyboardButton("❌ Refuser", callback_data=f"reject_{order_id}")
    ]]

    await context.bot.send_message(
        ADMIN_ID,
        f"🛎️ **Commande #{order_id}**\n@{user.username}\n\n{items_text}\n\n💰 {data['total']}€",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    await update.message.reply_text("⏳ Commande envoyée, attente validation.")

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, order_id = query.data.split("_")
    order_id = int(order_id)

    orders = load_orders()
    order = next(o for o in orders if o["id"] == order_id)

    if action == "accept":
        msg = "✅ Commande acceptée"
        order["status"] = "accepted"
    else:
        msg = "❌ Commande refusée"
        order["status"] = "rejected"

    save_orders(orders)

    await context.bot.send_message(order["user_id"], msg)
    await query.edit_message_text(msg)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, receive_order))
    app.add_handler(CallbackQueryHandler(admin_action))

    app.run_polling()

if __name__ == "__main__":
    main()
