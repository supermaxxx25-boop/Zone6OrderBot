let panier = {}

function add(produit) {
  panier[produit] = (panier[produit] || 0) + 1
  Telegram.WebApp.showPopup({
    title: "Ajouté",
    message: produit + " ajouté au panier",
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

  Telegram.WebApp.sendData(JSON.stringify(panier))
  Telegram.WebApp.close()
}
