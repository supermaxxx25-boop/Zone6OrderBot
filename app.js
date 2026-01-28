Telegram.WebApp.ready()

Telegram.WebApp.MainButton.setText("VALIDER TEST")
Telegram.WebApp.MainButton.show()

Telegram.WebApp.MainButton.onClick(() => {
  const testData = {
    "Burger": 2,
    "Pizza": 1
  }

  Telegram.WebApp.sendData(JSON.stringify(testData))
})
