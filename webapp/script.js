let cart = [];
let total = 0;

const tg = window.Telegram.WebApp;
tg.expand();

function addItem(name, price) {
  cart.push({ name, price });
  total += price;
  renderCart();
}

function renderCart() {
  const list = document.getElementById("cart");
  list.innerHTML = "";

  cart.forEach(item => {
    const li = document.createElement("li");
    li.textContent = `${item.name} - ${item.price} €`;
    list.appendChild(li);
  });

  document.getElementById("total").innerText = total;
}

function sendOrder() {
  if (cart.length === 0) {
    alert("Panier vide");
    return;
  }

  const order = {
    items: cart,
    total: total
  };

  tg.sendData(JSON.stringify(order));
  tg.close();
}
