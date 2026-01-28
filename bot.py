import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram.ext import ApplicationBuilder

from database import init_db
from handlers.start import register_start
from handlers.boutique import register_boutique
from handlers.panier import register_panier
from handlers.commande import register_commande


# =========================
# CONFIGURATION
# =========================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8348647959"))


# =========================
# SERVEUR HTTP (Railway)
# =========================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return


def run_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# =========================
# MAIN
# =========================
def main():
    if not TOKEN:
        raise RuntimeError("❌ BOT_TOKEN manquant dans les variables d'environnement")

    print("🔧 Initialisation de la base de données...")
    init_db()

    print("🌐 Démarrage du serveur HTTP...")
    threading.Thread(target=run_server, daemon=True).start()

    print("🤖 Lancement du bot Telegram...")
    app = ApplicationBuilder().token(TOKEN).build()

    register_start(app)
    register_boutique(app)
    register_panier(app)
    register_commande(app)

    print("✅ Bot en ligne et opérationnel")
    app.run_polling()


if __name__ == "__main__":
    main()
