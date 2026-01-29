const products = [
  {
    id: 1,
    name: "OG Kush CBD",
    category: "fleurs",
    price: 10,
    image: "https://via.placeholder.com/300x200",
    description: "Fleur CBD premium 🌿"
  },
  {
    id: 2,
    name: "Amnesia CBD",
    category: "fleurs",
    price: 12,
    image: "https://via.placeholder.com/300x200",
    description: "Puissante et relaxante"
  },
  {
    id: 3,
    name: "Résine Gold",
    category: "resines",
    price: 15,
    image: "https://via.placeholder.com/300x200",
    description: "Résine CBD haut de gamme"
  }
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
          <div class="card-content">
            <span class="badge">${p.category.toUpperCase()}</span>
            <h3>${p.name}</h3>
            <p>${p.description}</p>
            <p><b>${p.price}€</b></p>
            <button onclick="addToCart(${p.id})">Ajouter au panier</button>
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
  cartTotal.textContent = "Total : " + total + "€";
}

document.getElementById("cart-btn").onclick = openCart;
document.getElementById("categoryFilter").onchange = e => renderProducts(e.target.value);

renderProducts();
