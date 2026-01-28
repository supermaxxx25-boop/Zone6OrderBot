let panier = {}

// INITIALISATION OBLIGATOIRE
Telegram.WebApp.ready()

// CONFIGURATION DU BOUTON TELEGRAM
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

  console.log("PANIER ENVOYÉ:", panier)
  Telegram.WebApp.sendData(JSON.stringify(panier))
})

function add(produit) {
  panier[produit] = (panier[produit] || 0) + 1

  Telegram.WebApp.showPopup({
    title: "Ajouté",
    message: produit + " ajouté au panier",
    buttons: [{ type: "ok" }]
  })
}
