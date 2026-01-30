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
# MENU (NEUTRE)
# =====================
CATEGORIES = {
    "cat_a": {
        "nom": "📦 Catégorie A",
        "sous_categories": {
            "sub_a1": {
                "nom": "🧽 Gamme A1",
                "produits": {
                    "a1_p5": {"nom": "Format 5", "prix": 20},
                    "a1_p10": {"nom": "Format 10", "prix": 40},
                    "a1_p25": {"nom": "Format 25", "prix": 80},
                    "a1_p50": {"nom": "Format 50", "prix": 140},
                    "a1_p100": {"nom": "Format 100", "prix": 250},
                }
            },
            "sub_a2": {
                "nom": "⚡️ Gamme A2",
                "produits": {
                    "a2_p25": {"nom": "Format 25", "prix": 140},
                    "a2_p50": {"nom": "Format 50", "prix": 250},
                    "a2_p100": {"nom": "Format 100", "prix": 420},
                }
            }
        }
    },
    "cat_b": {
        "nom": "📦 Catégorie B",
        "sous_categories": {
            "sub_b1": {
                "nom": "🇺🇸 Gamme B1",
                "produits": {
                    "b1_p5": {"nom": "Format 5", "prix": 60},
                    "b1_p10": {"nom": "Format 10", "prix": 100},
                    "b1_p25": {"nom": "Format 25", "prix": 200},
                    "b1_p50": {"nom": "Format 50", "prix": 350},
                    "b1_p100": {"nom": "Format 100", "prix": 650},
                }
            }
        }
    }
}

# Aplatir le menu pour le panier
MENU = {
    pid: p
    for c in CATEGORIES.values()
    for sc in c["sous_categories"].values()
    for pid, p in sc["produits"].items()
}

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenue\n🛒 Tu peux commander ici 👇",
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

        username = f"@{user.username}" if user.username else "(sans username)"
        texte_admin = (
            "🆕 *NOUVELLE COMMANDE*\n\n"
            f"👤 {user.full_name}\n"
            f"🔗 {username}\n\n"
        )

        for k, qte in panier.items():
            texte_admin += f"{MENU[k]['nom']} x{qte}\n"

        texte_admin += f"\n💰 Total : {total} {DEVISE}"
        texte_admin += f"\n📍 Infos : {infos}"
        texte_admin += f"\n🆔 `{order_id}`"
        texte_admin += "\n\n⏳ *STATUT : EN ATTENTE*"

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
            "admin_message_id": msg_admin.message_id,
            "admin_texte": texte_admin
        }

        context.user_data.clear()
        return

    await start(update, context)

# =====================
# BOUTIQUE / PANIER
# =====================
async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    buttons = [
        [InlineKeyboardButton(c["nom"], callback_data=f"cat_{cid}")]
        for cid, c in CATEGORIES.items()
    ]
    buttons.append([InlineKeyboardButton("🛒 Panier", callback_data="panier")])
    await q.edit_message_text(
        "🍽️ *Menu*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def afficher_categorie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cid = q.data.replace("cat_", "")
    cat = CATEGORIES[cid]

    buttons = [
        [InlineKeyboardButton(sc["nom"], callback_data=f"sub_{cid}_{sid}")]
        for sid, sc in cat["sous_categories"].items()
    ]
    buttons.append([InlineKeyboardButton("⬅️ Retour", callback_data="boutique")])

    await q.edit_message_text(
        cat["nom"],
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def afficher_sous_categorie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, cid, sid = q.data.split("_", 2)
    sc = CATEGORIES[cid]["sous_categories"][sid]

    buttons = [
        [InlineKeyboardButton(p["nom"], callback_data=f"add_{pid}")]
        for pid, p in sc["produits"].items()
    ]
    buttons.append([InlineKeyboardButton("⬅️ Retour", callback_data=f"cat_{cid}")])

    await q.edit_message_text(
        sc["nom"],
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def ajouter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data.setdefault("panier", {})
    key = q.data.replace("add_", "")
    context.user_data["panier"][key] = context.user_data["panier"].get(key, 0) + 1
    await afficher_panier(q, context)

async def modifier_qte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action, key = q.data.split("_", 1)

    panier = context.user_data.get("panier", {})
    if key not in panier:
        return

    if action == "plus":
        panier[key] += 1
    else:
        panier[key] -= 1
        if panier[key] <= 0:
            panier.pop(key)

    await afficher_panier(q, context)

async def panier_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await afficher_panier(q, context)

async def afficher_panier(q, context):
    panier = context.user_data.get("panier", {})
    if not panier:
        await q.edit_message_text(
            "🛒 Panier vide",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Menu", callback_data="boutique")]
            ])
        )
        return

    texte = "🛒 *Ton panier*\n\n"
    boutons = []

    for k, qte in panier.items():
        texte += f"{MENU[k]['nom']} x{qte}\n"
        boutons.append([
            InlineKeyboardButton("➖", callback_data=f"moins_{k}"),
            InlineKeyboardButton("➕", callback_data=f"plus_{k}")
        ])

    texte += f"\n💰 Total : {calcul_total(panier)} {DEVISE}"

    boutons.append([InlineKeyboardButton("✅ Commander", callback_data="valider")])
    boutons.append([InlineKeyboardButton("⬅️ Menu", callback_data="boutique")])

    await q.edit_message_text(
        texte,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(boutons)
    )

async def valider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["attente_infos"] = True
    await q.edit_message_text(
        "Merci de nous fournir :\n\n- Ton adresse 📍\n\n- Ton numéro 📲"
    )

# =====================
# STATUTS
# =====================
def boutons_suivi(oid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ Préparation", callback_data=f"prep_{oid}")],
        [InlineKeyboardButton("🏎️ Livraison", callback_data=f"livraison_{oid}")],
        [InlineKeyboardButton("✅ Livrée", callback_data=f"livree_{oid}")]
    ])

async def update_admin(context, oid, statut, reply_markup=None):
    cmd = COMMANDES.get(oid)
    if not cmd:
        return

    base = cmd["admin_texte"].rsplit("\n\n", 1)[0]
    new_text = base + f"\n\n{statut}"

    await context.bot.edit_message_text(
        chat_id=ADMIN_ID,
        message_id=cmd["admin_message_id"],
        text=new_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    cmd["admin_texte"] = new_text

async def update_client(context, oid, statut):
    cmd = COMMANDES.get(oid)
    if not cmd:
        return

    panier = cmd["panier"]
    texte = "🧾 *Récap de ta commande*\n\n"
    for k, q in panier.items():
        texte += f"{MENU[k]['nom']} x{q}\n"

    texte += f"\n💰 Total : {calcul_total(panier)} {DEVISE}"
    texte += f"\n🆔 Commande : `{oid}`"
    texte += f"\n\n{statut}"

    await context.bot.edit_message_text(
        chat_id=cmd["client_id"],
        message_id=cmd["message_id"],
        text=texte,
        parse_mode="Markdown"
    )

# =====================
# ADMIN ACTIONS
# =====================
async def accepter_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    oid = q.data.replace("accept_", "")

    await update_client(context, oid, "🟢 *COMMANDE ACCEPTÉE*")
    await update_admin(context, oid, "🟢 *STATUT : COMMANDE ACCEPTÉE*", boutons_suivi(oid))

async def refuser_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    oid = q.data.replace("reject_", "")

    await update_client(context, oid, "🔴 *COMMANDE REFUSÉE*")
    await update_admin(context, oid, "🔴 *STATUT : COMMANDE REFUSÉE*")

async def suivi_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action, oid = q.data.split("_", 1)

    statuts = {
        "prep": "⏳ *STATUT : EN PRÉPARATION*",
        "livraison": "🏎️ *STATUT : EN LIVRAISON*",
        "livree": "✅ *STATUT : COMMANDE LIVRÉE*"
    }

    statut = statuts[action]

    await update_client(context, oid, statut)
    await update_admin(context, oid, statut, None if action == "livree" else boutons_suivi(oid))

# =====================
# ANNULATION CLIENT
# =====================
async def annuler_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    oid = q.data.replace("cancel_", "")

    await update_admin(context, oid, "❌ *COMMANDE ANNULÉE PAR LE CLIENT*")
    await q.edit_message_text("❌ *Commande annulée*", parse_mode="Markdown")

# =====================
# UTILS
# =====================
def calcul_total(panier):
    return sum(MENU[k]["prix"] * q for k, q in panier.items())

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(boutique, "^boutique$"))
    app.add_handler(CallbackQueryHandler(afficher_categorie, "^cat_"))
    app.add_handler(CallbackQueryHandler(afficher_sous_categorie, "^sub_"))
    app.add_handler(CallbackQueryHandler(ajouter, "^add_"))
    app.add_handler(CallbackQueryHandler(modifier_qte, "^(plus|moins)_"))
    app.add_handler(CallbackQueryHandler(panier_handler, "^panier$"))
    app.add_handler(CallbackQueryHandler(valider, "^valider$"))
    app.add_handler(CallbackQueryHandler(annuler_commande, "^cancel_"))
    app.add_handler(CallbackQueryHandler(accepter_commande, "^accept_"))
    app.add_handler(CallbackQueryHandler(refuser_commande, "^reject_"))
    app.add_handler(CallbackQueryHandler(suivi_commande, "^(prep|livraison|livree)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Bot actif")
    app.run_polling()

if __name__ == "__main__":
    main()
