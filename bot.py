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

COMMANDES = {}

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenue chez *Zone 6 Food*\n\n"
        "Commande facilement 👇",
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
    panier = context.user_data["panier"]
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
        sous_total = p["prix"] * qte
        texte += (
            f"{p['nom']}\n"
            f"➜ Quantité : {qte}\n"
            f"➜ Sous-total : {sous_total} €\n\n"
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
    panier = context.user_data["panier"]

    if action == "plus":
        panier[cle] += 1
    elif action == "moins":
        panier[cle] -= 1
        if panier[cle] <= 0:
            del panier[cle]
    elif action == "del":
        del panier[cle]

    await afficher_panier(q, context)

# =====================
# VALIDER
# =====================
async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.edit_message_text(
        "📍 *Merci de préciser :*\n"
        "• Adresse de livraison\n"
        "• Téléphone",
        parse_mode="Markdown"
    )
    context.user_data["attente_infos"] = True

# =====================
# INFOS CLIENT + COMMANDE
# =====================
async def infos_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("attente_infos"):
        return

    user = update.message.from_user
    panier = context.user_data["panier"]
    total = calcul_total(panier)
    infos = update.message.text
    order_id = str(uuid.uuid4())[:8]

    COMMANDES[order_id] = {
        "client_id": user.id,
        "client_nom": user.full_name,
        "panier": panier.copy(),
        "total": total
    }

    await update.message.reply_text(
        "⏳ *Commande envoyée*\n\n"
        "📲 Zone6 doit confirmer la commande.\n"
        "Tu recevras une notif rapidement 🙏",
        parse_mode="Markdown"
    )

    recap_client = (
        "🧾 *Récapitulatif de ta commande*\n\n"
        f"{resume_panier(panier)}\n"
        f"💰 *Total : {total} €*\n\n"
        "📍 *Infos fournies :*\n"
        f"{infos}\n\n"
        "⏳ En attente de confirmation par Zone6"
    )

    msg_recap = await update.message.reply_text(
        recap_client,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Annuler ma commande", callback_data=f"cancel_{order_id}")]
        ])
    )

    COMMANDES[order_id]["recap_message_id"] = msg_recap.message_id

    texte_admin = (
        f"🆕 *NOUVELLE COMMANDE*\n"
        f"🆔 `{order_id}`\n\n"
        f"👤 Client : {user.full_name}\n"
        f"🆔 Telegram : `{user.id}`\n\n"
        f"🧾 *DÉTAIL COMMANDE*\n"
        f"{resume_panier(panier)}\n"
        f"💰 *Total : {total} €*\n\n"
        f"📍 Infos client :\n{infos}"
    )

    await context.bot.send_message(
        ADMIN_ID,
        texte_admin,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Accepter", callback_data=f"accept_{order_id}"),
                InlineKeyboardButton("❌ Refuser", callback_data=f"refuse_{order_id}")
            ]
        ])
    )

    context.user_data.clear()

# =====================
# ANNULATION CLIENT
# =====================
async def annuler_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, order_id = q.data.split("_")
    cmd = COMMANDES.get(order_id)
    if not cmd:
        await q.edit_message_text("⚠️ Cette commande n'existe plus.")
        return

    del COMMANDES[order_id]

    await q.edit_message_text(
        "❌ *Ta commande a été annulée avec succès.*",
        parse_mode="Markdown"
    )

    await context.bot.send_message(
        ADMIN_ID,
        f"⚠️ *Commande annulée par le client*\n🆔 `{order_id}`",
        parse_mode="Markdown"
    )

# =====================
# ACCEPT / REFUSE
# =====================
async def decision_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    action, order_id = q.data.split("_")
    cmd = COMMANDES.get(order_id)
    if not cmd:
        return

    if action == "accept":
        # Supprimer le bouton Annuler côté client
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=cmd["client_id"],
                message_id=cmd.get("recap_message_id"),
                reply_markup=None
            )
        except:
            pass

        await q.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👨‍🍳 En préparation", callback_data=f"statut_prep_{order_id}")],
                [InlineKeyboardButton("🛵 En livraison", callback_data=f"statut_livraison_{order_id}")],
                [InlineKeyboardButton("✅ Livrée", callback_data=f"statut_livree_{order_id}")]
            ])
        )

        await context.bot.send_message(
            cmd["client_id"],
            "✅ *Ta commande a été acceptée et sera préparée rapidement* 🍽️",
            parse_mode="Markdown"
        )

    elif action == "refuse":
        await q.edit_message_text("❌ *Commande refusée*")

        await context.bot.send_message(
            cmd["client_id"],
            "❌ *Désolé, ta commande a été refusée.*\nContacte Zone6 🙏",
            parse_mode="Markdown"
        )

        del COMMANDES[order_id]

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
def calcul_total(panier):
    return sum(MENU[k]["prix"] * v for k, v in panier.items())

def resume_panier(panier):
    texte = ""
    for k, v in panier.items():
        p = MENU[k]
        texte += f"• {p['nom']} x{v} = {p['prix']*v} €\n"
    return texte

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
    app.add_handler(CallbackQueryHandler(annuler_commande, "^cancel_"))
    app.add_handler(CallbackQueryHandler(decision_commande, "^(accept|refuse)_"))
    app.add_handler(CallbackQueryHandler(statut_handler, "^statut_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, infos_client))

    print("🤖 Zone 6 Food — version finale (annulation désactivée après acceptation)")
    app.run_polling()

if __name__ == "__main__":
    main()
