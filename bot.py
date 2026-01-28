import os
import uuid
import logging
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
# LOGS
# =====================
logging.basicConfig(level=logging.INFO)

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

COMMANDES = {}

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenue chez *Zone 6 Food*\n\nCommande facilement 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Ouvrir la boutique", callback_data="boutique")]
        ])
    )

# =====================
# BOUTIQUE
# =====================
async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data.setdefault("panier", {})

    await q.edit_message_text(
        "🍽️ *Menu Zone 6 Food*\n\n"
        "🍔 Burger – 7 €\n"
        "🍕 Pizza – 10 €\n"
        "🍛 Riz poulet – 8 €\n\n"
        "👉 Clique pour ajouter au panier",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🍔 Burger", callback_data="add_burger"),
                InlineKeyboardButton("🍕 Pizza", callback_data="add_pizza")
            ],
            [InlineKeyboardButton("🍛 Riz", callback_data="add_riz")],
            [InlineKeyboardButton("🛒 Voir mon panier", callback_data="panier")]
        ])
    )

# =====================
# AJOUT PANIER
# =====================
async def ajouter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    produit = q.data.replace("add_", "")
    panier = context.user_data.setdefault("panier", {})
    panier[produit] = panier.get(produit, 0) + 1

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
        await q.edit_message_text(
            "🛒 *Ton panier est vide*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Retour menu", callback_data="boutique")]
            ])
        )
        return

    texte = "🛒 *Ton panier*\n\n"
    clavier = []

    for cle, qte in panier.items():
        p = MENU[cle]
        texte += (
            f"{p['nom']}\n"
            f"➜ Quantité : {qte}\n"
            f"➜ Sous-total : {p['prix'] * qte} €\n\n"
        )

        clavier.append([
            InlineKeyboardButton("➖", callback_data=f"moins_{cle}"),
            InlineKeyboardButton("➕", callback_data=f"plus_{cle}"),
            InlineKeyboardButton("🗑️ Retirer", callback_data=f"del_{cle}")
        ])

    total = calcul_total(panier)
    texte += f"💰 *Total : {total} €*"

    clavier.append([InlineKeyboardButton("✅ Confirmer la commande", callback_data="valider")])
    clavier.append([InlineKeyboardButton("⬅️ Continuer mes achats", callback_data="boutique")])

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

    action, cle = q.data.split("_")
    panier = context.user_data.get("panier", {})

    if action == "plus":
        panier[cle] += 1
    elif action == "moins":
        panier[cle] -= 1
        if panier[cle] <= 0:
            panier.pop(cle, None)
    elif action == "del":
        panier.pop(cle, None)

    await afficher_panier(q, context)

# =====================
# VALIDER
# =====================
async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["attente_infos"] = True

    await q.edit_message_text(
        "📍 *Merci de préciser :*\n"
        "• Adresse de livraison\n"
        "• Téléphone",
        parse_mode="Markdown"
    )

# =====================
# MESSAGE TEXTE
# =====================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("attente_infos"):
        await traiter_infos_client(update, context)
        return

    await update.message.reply_text(
        "🛒 Tu peux commander ici 👇",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍️ Ouvrir la boutique", callback_data="boutique")]
        ])
    )

# =====================
# TRAITEMENT COMMANDE
# =====================
async def traiter_infos_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    panier = context.user_data.get("panier", {})
    total = calcul_total(panier)
    infos = update.message.text
    order_id = str(uuid.uuid4())[:8]

    COMMANDES[order_id] = {
        "client_id": user.id,
        "panier": panier.copy(),
        "statut": "en_attente"
    }

    # RÉCAP CLIENT
    await update.message.reply_text(
        "📋 *Récapitulatif de ta commande*\n\n"
        f"{resume_panier(panier)}\n\n"
        f"💰 *Total : {total} €*\n"
        f"🆔 *Commande :* `{order_id}`\n\n"
        "⏳ En attente de validation par Zone 6 Food",
        parse_mode="Markdown"
    )

    # 🔗 PSEUDO TELEGRAM CLIQUABLE
    if user.username:
        contact = f"@{user.username}"
    else:
        contact = f"[Ouvrir le profil](tg://user?id={user.id})"

    # 🔴 ADMIN
    await context.bot.send_message(
        ADMIN_ID,
        f"🆕 *NOUVELLE COMMANDE*\n"
        f"🆔 `{order_id}`\n\n"
        f"👤 *Client :* {user.full_name}\n"
        f"📎 *Contact :* {contact}\n\n"
        f"{resume_panier(panier)}\n"
        f"💰 *Total : {total} €*\n\n"
        f"📍 Infos client :\n{infos}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Accepter", callback_data=f"admin_accept_{order_id}"),
                InlineKeyboardButton("❌ Refuser", callback_data=f"admin_refuse_{order_id}")
            ]
        ])
    )

    context.user_data.clear()

# =====================
# ADMIN : ACCEPTER
# =====================
async def admin_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    order_id = q.data.replace("admin_accept_", "")
    cmd = COMMANDES.get(order_id)
    if not cmd:
        return

    cmd["statut"] = "confirmee"

    await context.bot.send_message(
        cmd["client_id"],
        "✅ *Ta commande est acceptée !*\n👨‍🍳 Elle est en préparation.",
        parse_mode="Markdown"
    )

    await q.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👨‍🍳 En préparation", callback_data=f"statut_prep_{order_id}"),
                InlineKeyboardButton("🛵 En livraison", callback_data=f"statut_livraison_{order_id}")
            ],
            [InlineKeyboardButton("✅ Livrée", callback_data=f"statut_livree_{order_id}")]
        ])
    )

# =====================
# ADMIN : REFUSER
# =====================
async def admin_refuse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    order_id = q.data.replace("admin_refuse_", "")
    cmd = COMMANDES.get(order_id)
    if not cmd:
        return

    cmd["statut"] = "refusee"

    await context.bot.send_message(
        cmd["client_id"],
        "❌ *Ta commande a été refusée.*\n🙏 Désolé pour le désagrément.",
        parse_mode="Markdown"
    )

    await q.edit_message_reply_markup(reply_markup=None)

# =====================
# STATUT ADMIN
# =====================
async def statut_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, statut, order_id = q.data.split("_")
    cmd = COMMANDES.get(order_id)
    if not cmd or cmd["statut"] != "confirmee":
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
def calcul_total(panier):
    return sum(MENU[k]["prix"] * v for k, v in panier.items())

def resume_panier(panier):
    return "\n".join(
        f"• {MENU[k]['nom']} x{v} = {MENU[k]['prix']*v} €"
        for k, v in panier.items()
    )

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
    app.add_handler(CallbackQueryHandler(admin_accept, "^admin_accept_"))
    app.add_handler(CallbackQueryHandler(admin_refuse, "^admin_refuse_"))
    app.add_handler(CallbackQueryHandler(statut_handler, "^statut_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Zone 6 Food — bot opérationnel")
    app.run_polling()

if __name__ == "__main__":
    main()
