import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from produits import PRODUITS
from database import init_db, get_db

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 123456789  # ⬅️ remplace par TON ID Telegram


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Boutique", callback_data="boutique")],
        [InlineKeyboardButton("🧺 Mon panier", callback_data="panier")],
    ]
    await update.message.reply_text(
        "👋 Bienvenue sur la boutique ZONE 6\nPaiement à la livraison 🇫🇷",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    for pid, p in PRODUITS.items():
        await query.message.reply_photo(
            photo=p["image"],
            caption=f"🛍️ {p['nom']}\n💶 {p['prix']} €",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("➕ Ajouter au panier", callback_data=f"add_{pid}")]]
            ),
        )


async def add_panier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    panier = context.user_data.get("panier", [])
    panier.append(int(query.data.split("_")[1]))
    context.user_data["panier"] = panier

    await query.message.reply_text("✅ Produit ajouté au panier")


async def panier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    panier = context.user_data.get("panier", [])
    if not panier:
        await query.message.reply_text("🧺 Panier vide")
        return

    total = sum(PRODUITS[p]["prix"] for p in panier)
    recap = "\n".join(f"- {PRODUITS[p]['nom']}" for p in panier)

    await query.message.reply_text(
        f"🧾 Panier :\n{recap}\n\n💶 Total : {total} €",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ Commander", callback_data="commander")]]
        ),
    )


async def commander(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["step"] = "nom"
    await query.message.reply_text("✍️ Ton nom complet ?")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step == "nom":
        context.user_data["nom"] = update.message.text
        context.user_data["step"] = "tel"
        await update.message.reply_text("📞 Ton téléphone ?")

    elif step == "tel":
        context.user_data["tel"] = update.message.text
        context.user_data["step"] = "adresse"
        await update.message.reply_text("📍 Ton adresse ?")

    elif step == "adresse":
        context.user_data["adresse"] = update.message.text
        await enregistrer_commande(update, context)


async def enregistrer_commande(update, context):
    panier = context.user_data.get("panier", [])
    total = sum(PRODUITS[p]["prix"] for p in panier)
    recap = ", ".join(PRODUITS[p]["nom"] for p in panier)
    numero = f"CMD-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO commandes (numero, client, telephone, adresse, recap, total, statut, chat_id) VALUES (?,?,?,?,?,?,?,?)",
        (
            numero,
            context.user_data["nom"],
            context.user_data["tel"],
            context.user_data["adresse"],
            recap,
            total,
            "En attente",
            update.message.chat_id,
        ),
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Commande confirmée\n📦 {numero}\n💶 {total} €\n🚚 Paiement à la livraison"
    )

    await context.bot.send_message(
        ADMIN_ID,
        f"🆕 {numero}\n👤 {context.user_data['nom']}\n📞 {context.user_data['tel']}\n📍 {context.user_data['adresse']}\n🛍️ {recap}\n💶 {total} €",
    )

    context.user_data.clear()


def main():
    init_db()
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

def run_server():
    server = HTTPServer(("0.0.0.0", 8080), BaseHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(boutique, pattern="^boutique$"))
    app.add_handler(CallbackQueryHandler(panier, pattern="^panier$"))
    app.add_handler(CallbackQueryHandler(add_panier, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(commander, pattern="^commander$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
