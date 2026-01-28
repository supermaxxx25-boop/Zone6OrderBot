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

MENU = {
    "burger": {"nom": "🍔 Burger + frites", "prix": 7},
    "pizza": {"nom": "🍕 Pizza", "prix": 10},
    "riz": {"nom": "🍛 Riz sauce poulet", "prix": 8},
}

COMMANDES = {}  # order_id -> data

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clavier = [[InlineKeyboardButton("🛒 Ouvrir la boutique", callback_data="boutique")]]
    await update.message.reply_text(
        "👋 Bienvenue chez *Zone 6 Food*\nCommande en quelques clics 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# BOUTIQUE
# =====================
async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.setdefault("panier", {})

    await query.edit_message_text(
        "🍽️ *Menu Zone 6 Food*\n\n"
        "🍔 Burger – 7 €\n🍕 Pizza – 10 €\n🍛 Riz poulet – 8 €\n\n"
        "👉 Clique pour ajouter",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🍔 Burger", callback_data="add_burger"),
                InlineKeyboardButton("🍕 Pizza", callback_data="add_pizza")
            ],
            [InlineKeyboardButton("🍛 Riz", callback_data="add_riz")],
            [InlineKeyboardButton("🛒 Mon panier", callback_data="panier")]
        ])
    )

# =====================
# AJOUT PANIER
# =====================
async def ajouter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    p = q.data.replace("add_", "")
    panier = context.user_data["panier"]
    panier[p] = panier.get(p, 0) + 1
    await afficher_panier(q, context)

# =====================
# PANIER
# =====================
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
    clavier = []

    for k, v in panier.items():
        p = MENU[k]
        texte += f"{p['nom']} x{v} = {p['prix']*v} €\n"
        clavier.append([
            InlineKeyboardButton("➖", callback_data=f"moins_{k}"),
            InlineKeyboardButton("➕", callback_data=f"plus_{k}"),
            InlineKeyboardButton("🗑️", callback_data=f"del_{k}")
        ])

    texte += f"\n💰 *Total : {calcul_total(panier)} €*"

    clavier.append([InlineKeyboardButton("✅ Confirmer", callback_data="valider")])

    await q.edit_message_text(
        texte,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(clavier)
    )

# =====================
# MODIFIER PANIER
# =====================
async def modifier_panier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action, prod = q.data.split("_")
    panier = context.user_data["panier"]

    if action == "plus":
        panier[prod] += 1
    elif action == "moins":
        panier[prod] -= 1
        if panier[prod] <= 0:
            del panier[prod]
    elif action == "del":
        del panier[prod]

    await afficher_panier(q, context)

# =====================
# VALIDER
# =====================
async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📍 Envoie maintenant ton *adresse + téléphone*",
        parse_mode="Markdown"
    )
    context.user_data["attente_infos"] = True

# =====================
# INFOS CLIENT + COMMANDE
# =====================
async def infos_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("attente_infos"):
        return

    order_id = str(uuid.uuid4())[:8]
    panier = context.user_data["panier"]
    total = calcul_total(panier)
    user = update.message.from_user

    COMMANDES[order_id] = {
        "client_id": user.id,
        "panier": panier,
        "total": total
    }

    # Client
    msg = await update.message.reply_text(
        f"✅ *Commande confirmée*\n"
        f"🆔 `{order_id}`\n\n"
        "👨‍🍳 *Statut : En préparation*",
        parse_mode="Markdown"
    )

    # Admin
    await context.bot.send_message(
        ADMIN_ID,
        f"🆕 *Commande {order_id}*\n"
        f"Client : {user.full_name}\n"
        f"Total : {total} €",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👨‍🍳 Préparation", callback_data=f"statut_prep_{order_id}")],
            [InlineKeyboardButton("🛵 Livraison", callback_data=f"statut_livraison_{order_id}")],
            [InlineKeyboardButton("✅ Livrée", callback_data=f"statut_livree_{order_id}")]
        ])
    )

    context.user_data.clear()

# =====================
# STATUT ADMIN
# =====================
async def statut_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, statut, order_id = q.data.split("_")
    cmd = COMMANDES.get(order_id)
    if not cmd:
        return

    messages = {
        "prep": "👨‍🍳 *Commande en préparation*",
        "livraison": "🛵 *Commande en livraison*",
        "livree": "🎉 *Commande livrée*"
    }

    await context.bot.send_message(
        cmd["client_id"],
        messages[statut],
        parse_mode="Markdown"
    )

# =====================
# UTILS
# =====================
def calcul_total(p):
    return sum(MENU[k]["prix"] * v for k, v in p.items())

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(boutique, "^boutique$"))
    app.add_handler(CallbackQueryHandler(ajouter, "^add_"))
    app.add_handler(CallbackQueryHandler(panier_handler, "^panier$"))
    app.add_handler(CallbackQueryHandler(modifier_panier, "^(plus|moins|del)_"))
    app.add_handler(CallbackQueryHandler(valider, "^valider$"))
    app.add_handler(CallbackQueryHandler(statut_handler, "^statut_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, infos_client))

    print("🤖 Bot Zone 6 Food avec STATUTS actif")
    app.run_polling()

if __name__ == "__main__":
    main()
