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
# MENU AVEC SOUS-CATÉGORIES
# =====================
CATEGORIES = {
    "hash": {
        "nom": "🍫 HASH",
        "subs": {
            "mousse": {
                "nom": "🍫 Mousse",
                "produits": {
                    "mousse_5g": {"nom": "Mousse 5G", "prix": 20},
                    "mousse_10g": {"nom": "Mousse 10G", "prix": 40},
                    "mousse_25g": {"nom": "Mousse 25G", "prix": 80},
                    "mousse_50g": {"nom": "Mousse 50G", "prix": 150},
                    "mousse_100g": {"nom": "Mousse 100G", "prix": 250},
                }
            },
            "static": {
                "nom": "🍫 Static",
                "produits": {
                    "static_25g": {"nom": "Static 25G", "prix": 140},
                    "static_50g": {"nom": "Static 50G", "prix": 230},
                    "static_100g": {"nom": "Static 100G", "prix": 420},
                }
            }
        }
    },
    "weed": {
        "nom": "🍃 WEED",
        "subs": {
            "cali": {
                "nom": "🍃 Cali",
                "produits": {
                    "cali_5g": {"nom": "Cali 5G", "prix": 60},
                    "cali_10g": {"nom": "Cali 10G", "prix": 100},
                    "cali_25g": {"nom": "Cali 25G", "prix": 200},
                    "cali_50g": {"nom": "Cali 50G", "prix": 350},
                    "cali_100g": {"nom": "Cali 100G", "prix": 650},
                }
            }
        }
    }
}

# MENU FLATTEN
MENU = {}
for cat in CATEGORIES.values():
    for sub in cat["subs"].values():
        MENU.update(sub["produits"])

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenue dans la Zone6 👽\n🛒 Tu peux commander ici 👇",
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
        recap += "\n\n⏳ *STATUT : EN ATTENTE DE VALIDATION*"

        msg_client = await update.message.reply_text(
            recap,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Annuler la commande", callback_data=f"cancel_{order_id}")]
            ])
        )

        texte_admin = (
            "🆕 *NOUVELLE COMMANDE*\n\n"
            f"👤 {user.full_name}\n"
            f"🔗 @{user.username}\n\n"
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
# BOUTIQUE
# =====================
async def boutique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "🍽️ *Menu*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🍫 HASH", callback_data="cat_hash")],
            [InlineKeyboardButton("🍃 WEED", callback_data="cat_weed")],
            [InlineKeyboardButton("🛒 Panier", callback_data="panier")]
        ])
    )

async def afficher_categorie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cat_key = q.data.replace("cat_", "")
    cat = CATEGORIES[cat_key]

    boutons = [
        [InlineKeyboardButton(sub["nom"], callback_data=f"sub_{cat_key}_{k}")]
        for k, sub in cat["subs"].items()
    ]
    boutons.append([InlineKeyboardButton("⬅️ Retour", callback_data="boutique")])

    await q.edit_message_text(cat["nom"], reply_markup=InlineKeyboardMarkup(boutons))

async def afficher_subcategorie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, cat_key, sub_key = q.data.split("_", 2)

    sub = CATEGORIES[cat_key]["subs"][sub_key]

    boutons = [
        [InlineKeyboardButton(p["nom"], callback_data=f"add_{k}")]
        for k, p in sub["produits"].items()
    ]
    boutons.append([InlineKeyboardButton("⬅️ Retour", callback_data=f"cat_{cat_key}")])

    await q.edit_message_text(sub["nom"], reply_markup=InlineKeyboardMarkup(boutons))

# =====================
# PANIER
# =====================
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
    app.add_handler(CallbackQueryHandler(afficher_subcategorie, "^sub_"))
    app.add_handler(CallbackQueryHandler(ajouter, "^add_"))
    app.add_handler(CallbackQueryHandler(modifier_qte, "^(plus|moins)_"))
    app.add_handler(CallbackQueryHandler(panier_handler, "^panier$"))
    app.add_handler(CallbackQueryHandler(valider, "^valider$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Zone6 Food — Bot actif")
    app.run_polling()

if __name__ == "__main__":
    main()
