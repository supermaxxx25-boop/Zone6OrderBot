let panier = {}

// Initialisation Telegram
Telegram.WebApp.ready()

// Configuration du bouton Telegram
Telegram.WebApp.MainButton.setText("✅ Valider la commande")
Telegram.WebApp.MainButton.show()

Telegram.WebApp.MainButton.onClick(() => {
  if (Object.keys(panier).length === 0) {
    Telegram.WebApp.showPopup({
      title: "Panier vide",
      message: "Ajoute au moins un plat",
      buttons: [{ type: "ok" }]
    })
    return
  }

  // ENVOI DES DONNÉES AU BOT
  Telegram.WebApp.sendData(JSON.stringify(panier))

  // Optionnel : feedback visuel
  Telegram.WebApp.showPopup({
    title: "Commande envoyée",
    message: "Merci pour votre commande 🍽️",
    buttons: [{ type: "ok" }]
  })
})

function add(produit) {
  panier[produit] = (panier[produit] || 0) + 1

  Telegram.WebApp.showPopup({
    title: "Ajouté au panier",
    message: `${produit} × ${panier[produit]}`,
    buttons: [{ type: "ok" }]
  })
}
