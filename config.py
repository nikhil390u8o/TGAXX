import os

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", 29112886))
API_HASH = os.environ.get("API_HASH", "ce582d4fab1b31423b672046359056b4")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8748944729:AAEL1RffJcOmuy1QbyNJjBPcDA8aRng_zIM")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 7450385463))
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", -1002635720348))

# --- FORCE JOIN CONFIG ---
FORCE_JOIN_CHANNELS = [
    {"username": "log_tgx", "link": "https://t.me/log_tgx"},
    {"username": "sxypndu", "link": "https://t.me/sxypndu"},
    {"username": "sxyaru",  "link": "https://t.me/sxyaru"},
]

WELCOME_IMAGE = "https://files.catbox.moe/gcf6yz.jpg"
BASE_SESSION_DIR = "sessions"
SPAM_APPROVAL = {}
