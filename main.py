import os
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, BASE_SESSION_DIR
from database import init_db

# Shared state
login_data = {}

# Init
os.system("rm AXX_BOT.session 2>/dev/null")
os.system("rm AXX_BOT.session-journal 2>/dev/null")
os.system("rm database.db 2>/dev/null")
init_db()
os.makedirs(BASE_SESSION_DIR, exist_ok=True)

# Bot client
bot = Client(
    "AXX_BOT",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Register all handlers
from handlers.start import register_start
from handlers.deposit import register_deposit
from handlers.buy import register_buy
from handlers.admin import register_admin
from handlers.callbacks import register_callbacks
from handlers.inputs import register_inputs

register_start(bot)
register_deposit(bot)
register_buy(bot)
register_admin(bot, login_data)
register_callbacks(bot, login_data)
register_inputs(bot, login_data)

print("Bot is Starting...")
bot.run()
