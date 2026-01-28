Telegram.WebApp.ready()
Telegram.WebApp.expand()

function sendOrder() {
  const data = {
    Burger: 2,
    Pizza: 1
  }

  Telegram.WebApp.sendData(JSON.stringify(data))
}
