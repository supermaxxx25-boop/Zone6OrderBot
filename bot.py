import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8348647959  # remplace par TON vrai ID Telegram


# -------- COMMANDES --------

async def start(update, context):
    await update.message.reply_text("✅ Bot en ligne !")

    # TEST ADMIN
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="🧪 TEST : message admin OK"
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

    produits = {
        "Burger": ("Burger + frites", "3 500 FCFA"),
        "Pizza": ("Pizza", "5 000 FCFA"),
        "Riz": ("Riz sauce poulet", "4 000 FCFA"),
    }

    for key, (produit, prix) in produits.items():
        if key in text:
            context.user_data.clear()
            context.user_data["commande"] = produit

            await update.message.reply_text(
                f"🛒 *Commande :* {produit}\n"
                f"💰 *Prix :* {prix}\n\n"
                "Merci d’envoyer maintenant :\n"
                "📍 Adresse\n"
                "📞 Téléphone\n\n"
                "💵 Paiement à la livraison",
                parse_mode="Markdown"
            )
            return


async def finaliser_commande(update, context):
    if "commande" not in context.user_data:
        return  # pas encore de commande

    infos = update.message.text
    produit = context.user_data["commande"]

    # Client
    await update.message.reply_text(
        "✅ *Commande confirmée !*\n\n"
        f"🍽️ Plat : {produit}\n"
        f"📍 Infos : {infos}\n\n"
        "💵 Paiement à la livraison\n"
        "⏱️ Livraison en cours.\nMerci 🙏",
        parse_mode="Markdown"
    )

    # ADMIN
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📦 *NOUVELLE COMMANDE*\n\n"
            f"👤 Client : @{update.effective_user.username}\n"
            f"🍽️ Plat : {produit}\n"
            f"📍 Infos : {infos}"
        ),
        parse_mode="Markdown"
    )

    context.user_data.clear()

    # Message ADMIN
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📦 *NOUVELLE COMMANDE*\n\n"
            f"👤 Client : @{update.effective_user.username}\n"
            f"🍽️ Plat : {produit}\n"
            f"📍 Infos : {infos}"
        ),
        parse_mode="Markdown"
    )

    context.user_data.clear()

    # 🔔 MESSAGE ADMIN
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📦 *NOUVELLE COMMANDE*\n\n"
            f"👤 Client : @{update.effective_user.username}\n"
            f"🍽️ Plat : {produit}\n"
            f"📍 Infos : {infos}"
        ),
        parse_mode="Markdown"
    )

    context.user_data.clear()


# -------- MAIN --------

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN manquant")

    app = ApplicationBuilder().token(TOKEN).build()

    # Commandes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("boutique", boutique))

    # Messages texte (ordre IMPORTANT)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, finaliser_commande))

    print("✅ Bot en ligne")

    app.run_polling()

if __name__ == "__main__":
    main()
