let cart = [];
let total = 0;

const tg = window.Telegram.WebApp;
tg.expand();

function add(name, price) {
  cart.push(name + " - " + price + "€");
  total += price;
  render();
}

function render() {
  const list = document.getElementById("cart");
  list.innerHTML = "";
  cart.forEach(i => {
    const li = document.createElement("li");
    li.textContent = i;
    list.appendChild(li);
  });
  document.getElementById("total").innerText = total;
}

function send() {
  if (cart.length === 0) {
    alert("Panier vide");
    return;
  }

  tg.sendData(JSON.stringify({
    items: cart,
    total: total
  }));

  tg.close();
}
