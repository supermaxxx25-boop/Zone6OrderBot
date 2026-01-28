import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")


# -------- COMMANDES --------

async def start(update, context):
    await update.message.reply_text(
        "✅ Bot en ligne !\n"
        "Tape /boutique pour voir le menu 🍽️"
    )


async def boutique(update, context):
    await update.message.reply_text(
        "🍽️ *Menu Zone 6 Food*\n\n"
        "1️⃣ Burger + frites – 3 500 FCFA\n"
        "2️⃣ Pizza – 5 000 FCFA\n"
        "3️⃣ Riz sauce poulet – 4 000 FCFA\n\n"
        "👉 Choisis un plat",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["1️⃣ Burger", "2️⃣ Pizza"], ["3️⃣ Riz poulet"]],
            resize_keyboard=True
        )
    )


async def handle_order(update, context):
    text = update.message.text

    if "Burger" in text:
        produit = "Burger + frites"
        prix = "3 500 FCFA"
    elif "Pizza" in text:
        produit = "Pizza"
        prix = "5 000 FCFA"
    elif "Riz" in text:
        produit = "Riz sauce poulet"
        prix = "4 000 FCFA"
    else:
        return

    context.user_data["commande"] = produit

    await update.message.reply_text(
        f"🛒 *Commande :* {produit}\n"
        f"💰 *Prix :* {prix}\n\n"
        "Merci d’envoyer :\n"
        "• Adresse\n"
        "• Téléphone\n\n"
        "💵 Paiement à la livraison",
        parse_mode="Markdown"
    )


async def finaliser_commande(update, context):
    if "commande" not in context.user_data:
        return

    infos = update.message.text
    produit = context.user_data["commande"]

    await update.message.reply_text(
        "✅ *Commande confirmée !*\n\n"
        f"🍽️ Plat : {produit}\n"
        f"📍 Infos : {infos}\n\n"
        "⏱️ Livraison en cours.\nMerci 🙏",
        parse_mode="Markdown"
    )

    context.user_data.clear()


# -------- MAIN --------

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN manquant")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("boutique", boutique))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, finaliser_commande))

    app.run_polling()


if __name__ == "__main__":
    main()
