import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "bot.db")
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0")) or None

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi. .env faylida BOT_TOKEN=... qiymatini kiriting "
        "(.env faylidan nusxa oling)."
    )
