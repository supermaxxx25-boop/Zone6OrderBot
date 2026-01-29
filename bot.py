async def afficher_panier(q, context):
    panier = context.user_data.get("panier", {})

    texte = "🛒 *Ton panier*\n\n"

    if not panier:
        texte += "_Panier vide_\n"
    else:
        for k, qte in panier.items():
            texte += f"{MENU[k]['nom']} x{qte}\n"

    texte += f"\n💰 Total : {calcul_total(panier)} {DEVISE}"

    boutons = []

    for k in panier.keys():
        boutons.append([
            InlineKeyboardButton("➖", callback_data=f"minus_{k}"),
            InlineKeyboardButton("➕", callback_data=f"plus_{k}"),
            InlineKeyboardButton("🗑️", callback_data=f"del_{k}")
        ])

    boutons.append([
        InlineKeyboardButton("✅ Commander", callback_data="valider")
    ])
    boutons.append([
        InlineKeyboardButton("⬅️ Menu", callback_data="boutique")
    ])

    await q.edit_message_text(
        texte,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(boutons)
    )
