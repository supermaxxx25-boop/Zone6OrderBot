import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from produits import PRODUITS
from database import init_db, get_db
from datetime import datetime

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 123456789  # ⚠️ REMPLACE par ton ID Telegram (obligatoire)

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Boutique", callback_data="boutique")],
        [InlineKeyboardButton("🧺 Mon panier", callback_data="panier")],
    ]
    await update.message.reply_text(
        "👋 Bienvenue sur la boutique ZONE 6\n\nChoisis une option 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# --- BOUTIQUE ---
async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    for pid, p in PRODUITS.items():
        keyboard = [
            [InlineKeyboardButton("➕ Ajouter au panier", callback_data=f"add_{pid}")]
        ]
        await query.message.reply_photo(
            photo=p["image"],
            caption=f"🛍️ {p['nom']}\n💶 {p['prix']} €",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

# --- AJOUT PANIER ---
async def add_panier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pid = int(query.data.split("_")[1])
    panier = context.user_data.get("panier", [])
    panier.append(pid)
    context.user_data["panier"] = panier

    await query.message.reply_text("✅ Produit ajouté au panier")

# --- PANIER ---
async def panier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    panier = context.user_data.get("panier", [])
    if not panier:
        await query.message.reply_text("🧺 Ton panier est vide")
        return

    total = 0
    recap = ""
    for pid in panier:
        p = PRODUITS[pid]
        recap += f"- {p['nom']} ({p['prix']}€)\n"
        total += p["prix"]

    keyboard = [
        [InlineKeyboardButton("✅ Commander", callback_data="commander")]
    ]

    await query.message.reply_text(
        f"🧺 Ton panier :\n{recap}\n💶 Total : {total} €",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# --- COMMANDER ---
async def commander(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["step"] = "nom"
    await query.message.reply_text("✍️ Quel est ton nom complet ?")

# --- TEXTE CLIENT ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step == "nom":
        context.user_data["nom"] = update.message.text
        context.user_data["step"] = "tel"
        await update.message.reply_text("📞 Ton numéro de téléphone ?")

    elif step == "tel":
        context.user_data["tel"] = update.message.text
        context.user_data["step"] = "adresse"
        await update.message.reply_text("📍 Ton adresse complète (France) ?")

    elif step == "adresse":
        context.user_data["adresse"] = update.message.text
        await enregistrer_commande(update, context)

# --- ENREGISTRER COMMANDE ---
async def enregistrer_commande(update, context):
    panier = context.user_data.get("panier", [])
    total = sum(PRODUITS[pid]["prix"] for pid in panier)
    recap = ", ".join(PRODUITS[pid]["nom"] for pid in panier)

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
        f"✅ Commande confirmée !\n\n📦 Numéro : {numero}\n💶 Total : {total} €\n🚚 Paiement à la livraison"
    )

    # Notifier admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🆕 Nouvelle commande {numero}\n👤 {context.user_data['nom']}\n📞 {context.user_data['tel']}\n📍 {context.user_data['adresse']}\n🛍️ {recap}\n💶 {total} €",
    )

    context.user_data.clear()

# --- MAIN ---
def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(boutique, pattern="^boutique$"))
    app.add_handler(CallbackQueryHandler(panier, pattern="^panier$"))
    app.add_handler(CallbackQueryHandler(add_panier, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(commander, pattern="^commander$"))
    app.add_handler(CommandHandler("admin", lambda u, c: u.message.reply_text("Admin OK")))
    app.add_handler(CommandHandler("commandes", lambda u, c: u.message.reply_text("Voir DB")))
    app.add_handler(
        CallbackQueryHandler(panier, pattern="^panier$")
    )
    app.add_handler(
        CallbackQueryHandler(boutique, pattern="^boutique$")
    )
    app.add_handler(
        CallbackQueryHandler(add_panier, pattern="^add_")
    )
    app.add_handler(
        CallbackQueryHandler(commander, pattern="^commander$")
    )
    app.add_handler(
        CommandHandler("start", start)
    )
    app.add_handler(
        CommandHandler("help", start)
    )
    app.add_handler(
        CommandHandler("cancel", start)
    )
    app.add_handler(
        CommandHandler("menu", start)
    )
    app.add_handler(
        CommandHandler("panier", start)
    )
    app.add_handler(
        CommandHandler("boutique", start)
    )
    app.add_handler(
        CommandHandler("order", start)
    )
    app.add_handler(
        CommandHandler("shop", start)
    )
    app.add_handler(
        CommandHandler("store", start)
    )
    app.add_handler(
        CommandHandler("cmd", start)
    )
    app.add_handler(
        CommandHandler("commande", start)
    )
    app.add_handler(
        CommandHandler("orders", start)
    )
    app.add_handler(
        CommandHandler("
