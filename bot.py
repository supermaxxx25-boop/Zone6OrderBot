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

# ⚠️ REMPLACE par TON ID Telegram (obligatoire)
ADMIN_ID = 8348647959


# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Boutique", callback_data="boutique")],
        [InlineKeyboardButton("🧺 Mon panier", callback_data="panier")],
    ]
    await update.message.reply_text(
        "👋 Bienvenue sur la boutique ZONE 6\n\nPaiement à la livraison 🇫🇷\n\nChoisis une option 👇",
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


# --- GESTION TEXTE ---
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
async def enregistrer_commande(update: Update, context: ContextTypes.DEFAULT_TYPE):
    panier = context.user_data.get("panier", [])
    total = sum(PRODUITS[pid]["prix"] for pid in panier)
    recap = ", ".join(PRODUITS[pid]["nom"] for pid in panier)

    numero
