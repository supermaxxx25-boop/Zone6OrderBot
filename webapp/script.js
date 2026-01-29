Telegram.WebApp.ready();

const products = [
  { id: 1, name: "OG Kush CBD", price: 10, category: "fleurs", image: "https://via.placeholder.com/300" },
  { id: 2, name: "Amnesia CBD", price: 12, category: "fleurs", image: "https://via.placeholder.com/300" },
  { id: 3, name: "Résine Gold", price: 15, category: "resines", image: "https://via.placeholder.com/300" }
];

let cart = [];

const productsDiv = document.getElementById("products");
const cartDiv = document.getElementById("cart");
const cartCount = document.getElementById("cart-count");
const cartItems = document.getElementById("cart-items");
const cartTotal = document.getElementById("cart-total");

function renderProducts(filter = "all") {
  productsDiv.innerHTML = "";
  products
    .filter(p => filter === "all" || p.category === filter)
    .forEach(p => {
      productsDiv.innerHTML += `
        <div class="card">
          <img src="${p.image}">
          <div>
            <b>${p.name}</b>
            <p>${p.price}€</p>
            <button onclick="addToCart(${p.id})">Ajouter</button>
          </div>
        </div>
      `;
    });
}

function addToCart(id) {
  const product = products.find(p => p.id === id);
  cart.push(product);
  cartCount.textContent = cart.length;
}

function openCart() {
  cartDiv.classList.remove("hidden");
  renderCart();
}

function closeCart() {
  cartDiv.classList.add("hidden");
}

function renderCart() {
  cartItems.innerHTML = "";
  let total = 0;

  cart.forEach(p => {
    total += p.price;
    cartItems.innerHTML += `<p>${p.name} - ${p.price}€</p>`;
  });

  cartTotal.innerHTML = `
    <b>Total : ${total}€</b><br><br>
    <button onclick="sendOrder()">✅ Valider la commande</button>
  `;
}

function sendOrder() {
  Telegram.WebApp.sendData(JSON.stringify({
    items: cart,
    total: cart.reduce((s, p) => s + p.price, 0)
  }));
  Telegram.WebApp.close();
}

document.getElementById("cart-btn").onclick = openCart;
document.getElementById("categoryFilter").onchange = e => renderProducts(e.target.value);

renderProducts();
