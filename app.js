let panier = {}

// OBLIGATOIRE
Telegram.WebApp.ready()

function add(produit) {
  panier[produit] = (panier[produit] || 0) + 1

  Telegram.WebApp.showPopup({
    title: "Ajouté au panier",
    message: produit + " ajouté",
    buttons: [{ type: "ok" }]
  })
}

function envoyer() {
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
}
