import os
import sys

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN manquant")
    sys.exit(1)

if not ADMIN_ID:
    print("❌ ADMIN_ID manquant")
    sys.exit(1)

if not WEBAPP_URL:
    print("❌ WEBAPP_URL manquant")
    sys.exit(1)

ADMIN_ID = int(ADMIN_ID)
