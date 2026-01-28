let panier = {}

function add(produit) {
  panier[produit] = (panier[produit] || 0) + 1
  alert(produit + " ajouté")
}

function envoyer() {
  Telegram.WebApp.sendData(JSON.stringify(panier))
  Telegram.WebApp.close()
}
