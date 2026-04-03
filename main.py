import os
import random
import asyncio
import aiohttp
import sqlite3
import shutil
import re
import urllib.parse
from pyrogram import Client, filters, types, errors
from pyrogram.errors import SessionPasswordNeeded
from pyrogram.raw import functions, types as raw_types
from pyrogram.errors import RPCError, UserIsBlocked, FloodWait

# --- CONFIGURATION ---
API_ID = 29112886
API_HASH = "ce582d4fab1b31423b672046359056b4"
BOT_TOKEN = "8748944729:AAESwFP6f10NLfIi9lDptTNfcRlEbFH-2cQ"
ADMIN_ID = "8748944729:AAHG5Rxmuh1NrBg7dELW9_IAtT7cTX8mRfo"
MERCHANT_KEY = "WHQYNJ64618712357090"
LOG_CHANNEL_ID = -1002635720348
DEPOSIT_LOG_ID = -1003592661456
SPAM_APPROVAL = {}

# --- FORCE JOIN CONFIG ---
FORCE_JOIN_CHANNELS = [
    {"username": "axx_log", "link": "https://t.me/log_tgx"},
    {"username": "sxypndu", "link": "https://t.me/sxypndu"},
    {"username": "sxyaru", "link": "https://t.me/sxyaru"},
]
WELCOME_IMAGE = "https://i.ibb.co/Rp8FkFCk/photo-2026-03-17-13-58-26-7618223912299528208.jpg"

bot = Client(
    "AXX_BOT",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN)
login_data = {}
user_deposits = {}

os.system("rm TGKingRobot.session ")
os.system("rm TGKingRobot.session-journal ")
os.system("rm database.db")

# ================= DATABASE SETUP =================


def get_db():
    return sqlite3.connect("database.db", timeout=60, check_same_thread=False)


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        balance REAL DEFAULT 0,
        total_spent REAL DEFAULT 0,
        total_deposited REAL DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_name TEXT,
    status INTEGER DEFAULT 0,
    country TEXT,
    price REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    password TEXT,
    last_otp TEXT
)""")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("""
CREATE TABLE IF NOT EXISTS country_prices (
    country TEXT PRIMARY KEY,
    price REAL
)
""")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS business_stats (key TEXT PRIMARY KEY, value REAL)")
    cur.execute("INSERT OR IGNORE INTO settings VALUES ('price','100')")
    cur.execute(
        "INSERT OR IGNORE INTO business_stats VALUES ('total_sold',0), ('total_revenue',0), ('total_deposited',0)")
    conn.commit()
    conn.close()


init_db()
BASE_SESSION_DIR = "sessions"
os.makedirs(BASE_SESSION_DIR, exist_ok=True)

# --- DATABASE HELPERS ---


def get_user_data(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT balance, total_spent, total_deposited FROM users WHERE id=?",
        (user_id,))
    res = cur.fetchone()
    if not res:
        cur.execute("INSERT INTO users VALUES (?,0,0,0)", (user_id,))
        conn.commit()
        conn.close()
        return (0, 0, 0)
    conn.close()
    return res


def update_user_stats(user_id, balance_delta=0, spent_delta=0, deposit_delta=0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET balance = balance + ?, total_spent = total_spent + ?, total_deposited = total_deposited + ? WHERE id = ?",
        (balance_delta, spent_delta, deposit_delta, user_id))
    conn.commit()
    conn.close()


def update_biz_stats(key, amount):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE business_stats SET value = value + ? WHERE key=?", (amount, key))
    conn.commit()
    conn.close()


def get_setting(key):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res else "100"


def get_country_price(country):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT price FROM country_prices WHERE country=?", (country,))
    row = cur.fetchone()
    conn.close()
    if row:
        return float(row[0])
    return float(get_setting("price"))


def set_country_price(country, price):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO country_prices (country, price)
    VALUES (?, ?)
    ON CONFLICT(country) DO UPDATE SET price=excluded.price
    """, (country, price))
    conn.commit()
    conn.close()



# --- FORCE JOIN HELPER ---

async def check_force_join(client, user_id):
    not_joined = []
    for ch in FORCE_JOIN_CHANNELS:
        try:
            member = await client.get_chat_member(ch["username"], user_id)
            status = str(member.status).lower()
            if any(s in status for s in ("left", "kicked", "banned")):
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    return not_joined


# --- USER HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start_h(c, m):
    uid = m.from_user.id
    get_user_data(uid)

    not_joined = await check_force_join(c, uid)

    if not_joined:
        buttons = [
            [types.InlineKeyboardButton(f"𝐉𝐎𝐈𝐍 𝐂𝐇𝐀𝐍𝐍𝐄𝐋 {i+1}", url=ch["link"])]
            for i, ch in enumerate(not_joined)
        ]
        buttons.append([
            types.InlineKeyboardButton("𝐕𝐄𝐑𝐈𝐅𝐘", callback_data="verify_join")
        ])
        await m.reply_photo(
            photo=WELCOME_IMAGE,
            caption=(
                "**👑ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀʀᴜ ᴏᴛᴘ ʙᴏᴛ**\n\n"
                "**ᴛʜᴇ ᴍᴏsᴛ ᴛʀᴜsᴛᴇᴅ ғᴏʀ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛs**\n\n"
                "━━━━━━━━━━━━━━━\n"
                "⚠️ **ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ɢᴇᴛ ᴠᴇʀɪғʏ ᴛᴏ ᴜsᴇ ᴍᴇ**"
            ),
            reply_markup=types.InlineKeyboardMarkup(buttons)
        )
        return

    kb = types.ReplyKeyboardMarkup(
        [["Buy Account", "Profile"], ["Deposit", "My Stats"], ["Support"]],
        resize_keyboard=True
    )
    await m.reply_photo(
        photo=WELCOME_IMAGE,
        caption=(
            "**👑ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀʀᴜ ᴏᴛᴘ ʙᴏᴛ**\n\n"
            "**ᴛʜᴇ ᴍᴏsᴛ ᴛʀᴜsᴛᴇᴅ ғᴏʀ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛs**\n\n"
            "━━━━━━━━━━━━━━━\n"
            "✅ **ɴᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴍᴇ ғʀᴇᴇʟʏ**"
        ),
        reply_markup=kb
    )

# --- SUPPORT HANDLER ---

@bot.on_message(filters.regex("Support") & filters.private)
async def support_h(c, m):
    support_text = (
        "**🛡 ᴀʀᴜ ᴏᴛᴘ ʙᴏᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ**\n\n"
        "**⚠️ ᴀʟʟ ᴘᴜʀᴄʜᴀsᴇ ᴀʀᴇ ғɪɴᴀʟ ɴᴏ ʀᴇғᴜɴᴅs ᴀɴᴅ ɴᴏ ʀᴇᴘʟᴀᴄᴇᴍᴇɴᴛ**"
    )
    kb = types.InlineKeyboardMarkup([[
        types.InlineKeyboardButton("💬 Support", url="https://t.me/sxyaru")
    ]])
    await m.reply(support_text, reply_markup=kb)


# --- DEPOSIT SYSTEM ---

@bot.on_message(filters.regex("Deposit") & filters.private)
async def deposit_init(c, m):
    uid = m.from_user.id

    upi_id = "nikhil-bby@fam"
    ref_id = f"REF{random.randint(1000, 9999)}"

    upi_link = f"upi://pay?pa={upi_id}&pn=TGKing&tn={ref_id}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={urllib.parse.quote(upi_link)}"

    # Step 1 of deposit: show QR → wait for SS directly
    login_data[uid] = {"step": "dep_wait_ss", "ref": ref_id}

    await m.reply_photo(
        photo=qr_url,
        caption=(
            f"**💸 ᴅᴇᴘᴏsɪᴛ ᴠɪᴀ ᴜᴘɪ**\n\n"
            f"🏦 **ᴜᴘɪ ɪᴅ:** `{upi_id}`\n"
            f"📝 **ʀᴇғ ᴄᴏᴅᴇ:** `{ref_id}`\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✅ **ᴀғᴛᴇʀ ᴘᴀʏɪɴɢ:**\n"
            f"📸 **sᴇɴᴅ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ (photo)**"
        )
    )


# --- PROFILE ---

@bot.on_message(filters.regex("Profile") & filters.private)
async def profile_h(c, m):
    uid = m.from_user.id
    data = get_user_data(uid)
    await m.reply(
        f"👤 **ɴᴀᴍᴇ:** {m.from_user.first_name}\n"
        f"🆔 **ᴜsᴇʀ ɪᴅ:** `{uid}`\n"
        f"💰 **ʙᴀʟᴀɴᴄᴇ:** `₹{data[0]:.2f}`"
    )


# --- MY STATS ---

@bot.on_message(filters.regex("My Stats") & filters.private)
async def user_stats_h(c, m):
    uid = m.from_user.id
    bal, spent, dep = get_user_data(uid)
    conn = get_db()
    cur = conn.cursor()
    count = cur.execute(
        "SELECT COUNT(*) FROM orders WHERE user_id = ?", (uid,)).fetchone()[0]
    conn.close()
    text = (
        f"**📊 ʏᴏᴜʀ sᴛᴀᴛɪsᴛɪᴄs**\n\n"
        f"✅ **ᴀᴄᴄᴏᴜɴsᴛ ʙᴏᴜɢʜᴛ:** `{count}`\n"
        f"💰 **ᴛᴏᴛᴀʟ sᴘᴇɴᴛ:** `₹{spent:.2f}`\n"
        f"📥 **ᴛᴏᴛᴀʟ ᴅᴇᴘᴏsɪᴛᴇᴅ:** `₹{dep:.2f}`"
    )
    kb = types.InlineKeyboardMarkup([[
        types.InlineKeyboardButton("📋 ᴠɪᴇᴡ ʜɪsʏᴏʀʏ", callback_data="user_history")
    ]])
    await m.reply(text, reply_markup=kb)


# --- BUY ACCOUNT ---

@bot.on_message(filters.regex("Buy Account") & filters.private)
async def buy_acc_start(c, m):
    uid = m.from_user.id

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT session_name FROM orders WHERE user_id = ? AND status = 0", (uid,))
    existing_order = cur.fetchone()
    conn.close()

    if existing_order:
        return await m.reply("⚠️ **ʏᴏᴜ ʜᴀᴠᴇ ᴘᴇɴᴅɪɴɢ ᴏʀᴅᴇʀ!\n ғɪɴɪsʜ ɪᴛ ғɪʀsᴛ!**")

    countries = [
        d for d in os.listdir(BASE_SESSION_DIR)
        if os.path.isdir(os.path.join(BASE_SESSION_DIR, d))
    ]

    if not countries:
        return await m.reply("**❌ ɴᴏ sᴛᴏᴄᴋ ᴀᴠᴀɪʟᴀʙᴇ ᴄᴜʀʀᴇɴᴛʟʏ.**")

    buttons = []
    for country in countries:
        country_path = os.path.join(BASE_SESSION_DIR, country)
        count = len([f for f in os.listdir(country_path) if f.endswith(".session")])
        if count > 0:
            price = get_country_price(country)
            buttons.append([
                types.InlineKeyboardButton(
                    f"🌍 {country}  |  ₹{price}  |  {count} left",
                    callback_data=f"sel_{country}"
                )
            ])

    if not buttons:
        return await m.reply("**❌ ɴᴏ sᴛᴏᴄᴋ ᴀᴠᴀɪʟᴀʙᴇ ᴄᴜʀʀᴇɴᴛʟʏ.**")

    await m.reply(
        "**🌍 sᴇʟᴇᴄᴛ ᴀ ᴄᴏᴜɴᴛʀʏ:**",
        reply_markup=types.InlineKeyboardMarkup(buttons)
    )


# --- ADMIN PANEL ---

@bot.on_message(filters.command("admin") & filters.private)
async def admin_panel(c, m):
    uid = m.from_user.id
    if uid != ADMIN_ID:
        return await m.reply("❌ **ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ᴀᴅᴍɪɴ ʙɪᴛᴄʜ.**")

    price = get_setting("price")
    kb = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton(f"💲 Default Price | ₹{price}", callback_data="adm_setprice")],
        [types.InlineKeyboardButton("➕ Add Balance", callback_data="adm_addbal_init")],
        [
            types.InlineKeyboardButton("📊 Stats", callback_data="adm_stats"),
            types.InlineKeyboardButton("➕ Add Account", callback_data="adm_addacc")
        ],
        [types.InlineKeyboardButton("🌍 Set Country Price", callback_data="adm_country_price")],
        [types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast_init")],
        [types.InlineKeyboardButton("🔢 Manage Numbers", callback_data="adm_manage_numbers")]
    ])
    await m.reply("**🔧 ᴀᴅᴍɪɴ.ᴘᴀɴᴇʟ**", reply_markup=kb)


@bot.on_message(filters.command("approve_") & filters.private)
async def approve_spam(bot, m):
    if m.from_user.id != ADMIN_ID:
        return
    phone = m.text.split("_", 1)[1]
    SPAM_APPROVAL[phone] = True
    await m.reply(f"✅ `{phone}` **Approved! Continuing...**")


@bot.on_message(filters.command("skip_") & filters.private)
async def skip_spam(bot, m):
    if m.from_user.id != ADMIN_ID:
        return
    phone = m.text.split("_", 1)[1]
    SPAM_APPROVAL[phone] = False
    await m.reply(f"⏭ `{phone}` **Skipped!**")


# --- ALL CALLBACKS ---

@bot.on_callback_query()
async def handle_all_callbacks(c, q):
    uid = q.from_user.id
    data = q.data

    # ── Verify force join ──
    if data == "verify_join":
        not_joined = await check_force_join(c, uid)
        if not_joined:
            buttons = [
                [types.InlineKeyboardButton(f"📢 𝐉𝐎𝐈𝐍 𝐂𝐇𝐀𝐍𝐍𝐄𝐋 {i+1}", url=ch["link"])]
                for i, ch in enumerate(not_joined)
            ]
            buttons.append([
                types.InlineKeyboardButton("𝐕𝐄𝐑𝐈𝐅𝐘", callback_data="verify_join")
            ])
            await q.answer("❌ 𝐉𝐎𝐈𝐍 𝐊𝐀𝐑𝐎 𝐍𝐀 𝐐𝐓 😒!", show_alert=True)
            await q.message.edit_reply_markup(
                reply_markup=types.InlineKeyboardMarkup(buttons)
            )
            return

        # All joined — delete join message, send main menu
        await q.message.delete()
        kb = types.ReplyKeyboardMarkup(
            [["Buy Account", "Profile"], ["Deposit", "My Stats"], ["Support"]],
            resize_keyboard=True
        )
        await bot.send_photo(
            uid,
            photo=WELCOME_IMAGE,
            caption=(
                "**🔥ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀʀᴜ ᴏᴛᴘ ʙᴏᴛ!**\n\n"
                "**ᴛʜᴇ ᴍᴏsᴛ ᴛʀᴜsᴛᴇᴅ ʙᴏᴛ ғᴏʀ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛs**\n\n"
                "━━━━━━━━━━━━━━━\n"
                "✅ ʏᴏᴜ ᴀʀᴇ ᴠᴇʀɪғʏ:**"
            ),
            reply_markup=kb
        )
        return

    # ── Country selection ──
    if data.startswith("sel_"):
        country = data.split("_", 1)[1]
        price = get_country_price(country)
        kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("✅ Confirm & Buy", callback_data=f"conf_{country}")],
            [types.InlineKeyboardButton("🔙 Back", callback_data="back_to_buy")]
        ])
        await q.message.edit_text(
            f"**🛒 ᴄᴏɴғɪʀᴍ ᴘᴜʀᴄʜᴀsᴇ**\n\n"
            f"🌍 **ᴄᴏᴜɴᴛʀʏ:** {country}\n"
            f"💰 **ᴘʀɪᴄᴇ:** `₹{price}`\n\n"
            f"**ᴄʟɪᴄᴋ ᴄᴏɴғɪʀᴍ ᴛᴏ ɢᴇᴛ ᴀᴄᴄᴏᴜɴᴛ!**",
            reply_markup=kb
        )

    # ── Admin approves deposit — ask how much to add ──
    elif data.startswith("aprv_pay_"):
        parts = data.split("_")
        # format: aprv_pay_{uid}_{amount}
        target_uid = int(parts[2])
        claimed_amt = parts[3] if len(parts) > 3 else "?"
        login_data[uid] = {
            "step": "adm_confirm_amt",
            "target_uid": target_uid,
            "claimed": claimed_amt
        }
        await q.message.edit_text(
            f"✅ **ᴅᴇᴘᴏsɪᴛ ʀᴇǫᴜᴇsᴛ**\n"
            f"💰 **ᴜsᴇʀ ᴄʟᴀɪᴍᴇᴅ:** `₹{claimed_amt}`\n\n"
            f"**ᴇɴᴛᴇʀ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ᴛᴏ ᴀᴅᴅ (ɴᴜᴍʙᴇʀ ᴏɴʟʏ):**"
        )

    # ── Admin rejects deposit ──
    elif data.startswith("rej_pay_"):
        target_uid = int(data.split("_")[2])
        await q.message.edit_text("❌ **Payment Rejected.**")
        try:
            await bot.send_message(
                target_uid,
                "❌ **ʏᴏᴜʀ ᴅᴇᴘᴏsɪᴛ ɪs ʀᴇᴊᴇᴄᴛᴇᴅ**\n"
                "ɪғ ᴛʜɪs ɪs ᴀ ᴍɪsᴛᴀᴋᴇ ᴘʟs ᴄᴏɴᴛᴀᴄᴛ ᴛᴏ sᴜᴘᴘᴏʀᴛ."
            )
        except BaseException:
            pass

    # ── Confirm buy ──
    elif data.startswith("conf_"):
        country = data.split("_", 1)[1]
        price = get_country_price(country)
        bal, _, _ = get_user_data(uid)
        if bal < price:
            return await q.answer("❌ ɪɴsᴜғɪᴄɪᴀɴᴛ ʙᴀʟᴀɴᴄᴇ!", show_alert=True)

        c_path = os.path.join(BASE_SESSION_DIR, country)
        sessions = [f for f in os.listdir(c_path) if f.endswith(".session")]
        if not sessions:
            return await q.answer("❌ ɴᴏ sᴛᴏᴄᴋ ᴀᴠᴀɪʟᴀʙᴇ ᴄᴜʀʀᴇɴᴛʟʏ.", show_alert=True)

        s_name = sessions[0]
        phone_num = s_name.replace(".session", "")
        update_user_stats(uid, balance_delta=-price, spent_delta=price)
        update_biz_stats("total_sold", 1)
        update_biz_stats("total_revenue", price)

        acc_pass = "nikitayt7"
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (user_id, session_name, status, country, price, password) VALUES (?, ?, 0, ?, ?, ?)",
            (uid, s_name, country, price, acc_pass)
        )
        conn.commit()
        conn.close()

        # Half number for log: show first 6 digits + ****
        half_num = phone_num[:6] + "****" if len(phone_num) >= 6 else phone_num

        kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("📩 ɢᴇᴛ ᴏᴛᴘ", callback_data=f"get_{s_name}")]
        ])
        await q.message.edit_text(
            f"✅ **ᴏʀᴅᴇʀ ᴀᴄᴛɪᴠᴇ!**\n\n"
            f"📞 **ᴘʜᴏɴᴇ:** `{phone_num}`\n"
            f"🌍 **ᴄᴏᴜɴᴛʀʏ:** {country}\n\n"
            f"**📋 ɪɴsᴛʀᴜᴄᴛɪᴏɴ:**\n"
            f"1. ᴏᴘᴇɴ ᴛᴇʟᴇɢʀᴀɴ - ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛt\n"
            f"2. ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴜᴍʙᴇʀ\n"
            f"3. ᴄʟɪᴄᴋ **ɢᴇᴛ ᴏᴛᴘ** **ᴀғᴛᴇʀ ᴏᴛᴘ ᴀʀʀɪᴠᴇs\n"
            f"4. ᴜsᴇ ɴɪᴄᴇɢʀᴀᴍ ᴏʀ ᴛᴇʟᴇɢʀᴀᴍ x ғᴏʀ sᴀғᴇ ʟᴏɢɪɴ ᴡᴇ ᴀʀᴇ ɴᴏᴛ ʀᴇsᴘᴏɴsɪʙʟᴇ ғᴏʀ ᴀɴʏ ғʀᴇᴇᴢᴇ/ʙᴀɴ",

            reply_markup=kb
        )

        username = f"@{q.from_user.username}" if q.from_user.username else "No username"

        # Log channel message
        await bot.send_message(
            int(LOG_CHANNEL_ID),
            f"**ᴀᴄᴄᴏᴜɴᴛ sᴇʟʟᴇᴅ** ✅\n\n"
            f"**ᴜsᴇʀ** -- `{q.from_user.id}\n"
            f"**ᴜsᴇʀɴᴀᴍᴇ** -- `({username})`\n"
            f"**ᴄᴏᴜɴᴛʀʏ** -- {country}\n"
            f"**ɴᴜᴍʙ** -- `{half_num}`\n"
            f"**ᴘʀɪᴄᴇ** -- ₹{price}\n"
            f"**ᴊᴏɪɴ** -- @SXYPNDU\n"
        )

    # ── Back to buy ──
    elif data == "back_to_buy":
        await q.message.delete()
        await buy_acc_start(c, q.message)

    # ── Get OTP ──
    elif data.startswith("get_"):
        s_name = data.replace("get_", "")
        phone_display = s_name.replace(".session", "")

        conn = get_db()
        cur = conn.cursor()
        order = cur.execute(
            "SELECT country, password, last_otp FROM orders WHERE user_id = ? AND session_name = ?",
            (uid, s_name)
        ).fetchone()
        conn.close()

        if not order:
            return await q.answer("ᴏʀᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!", show_alert=True)

        country, password, last_otp = order

        full_path = ""
        for r, _, f in os.walk(BASE_SESSION_DIR):
            if s_name in f:
                full_path = os.path.join(r, s_name).replace(".session", "")
                break

        if not full_path or not os.path.exists(f"{full_path}.session"):
            kb = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("🔄 ɢᴇᴛ ᴏᴛᴘ ᴀɢᴀɪɴ", callback_data=f"get_{s_name}")],
                [types.InlineKeyboardButton("🚪 ʟᴏɢᴏᴜᴛ ғʀᴏᴍ ʙᴏᴛ", callback_data=f"ask_log_{s_name}")]
            ])
            await q.message.edit_text(
                f"⚠️ **ʙᴏᴛ ɪs ᴀʟʀᴇᴅʏ ʟᴏɢɢᴇᴅ ᴏᴜᴛ!**\n\n"
                f"📞 **ᴘʜᴏɴᴇ:** `{phone_display}`\n"
                f"🌍 **ᴄᴏᴜɴᴛʀʏ:** {country}\n"
                f"🔐 **ᴘᴀss:** `{password}`",
                reply_markup=kb
            )
            return

        temp_client = Client(name=full_path, api_id=API_ID, api_hash=API_HASH, no_updates=True)
        try:
            await temp_client.start()
            otp_found = None
            async for msg in temp_client.get_chat_history(777000, limit=1):
                if msg.text:
                    found = re.findall(r'\b\d{5}\b', msg.text)
                    if found:
                        otp_found = found[0]
                        break

            if not otp_found:
                return await q.answer("❌ ᴏᴛᴘ ɴᴏᴛ ғᴏᴜɴᴅ sᴇɴᴅ ᴏᴛᴘ ʙɪᴛᴄʜ ⚡.", show_alert=True)

            if last_otp == otp_found:
                return await q.answer("⚠️ sᴀᴍᴇ ᴏᴛᴘ sᴇɴᴅ ᴀ ɴᴇᴡ ᴏᴛᴘ.", show_alert=True)

            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "UPDATE orders SET last_otp=?, status=1 WHERE user_id=? AND session_name=?",
                (otp_found, uid, s_name)
            )
            conn.commit()
            conn.close()

            kb = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("🔄 ʀᴇᴅʀᴇsʜ ᴏᴛᴘ", callback_data=f"get_{s_name}")],
                [types.InlineKeyboardButton("🚪 ʟᴏɢᴏᴜᴛ ғʀᴏᴍ ʙᴏᴛ", callback_data=f"ask_log_{s_name}")]
            ])
            await q.message.edit_text(
                f"✅ **ᴏʀᴅᴇʀ ᴄᴏᴍᴘʟᴛᴇᴅ!**\n\n"
                f"📞 **ᴘʜᴏɴᴇ:** `{phone_display}`\n"
                f"🌍 **ᴄᴏᴜɴᴛʀʏ:** {country}\n"
                f"🔑 **ᴏᴛᴘ:** `{otp_found}`\n"
                f"🔐 **2ғᴀ:** `{password}`\n\n"
                f"⚠️ **ᴄʟɪᴄᴋ ʟᴏɢᴏᴜᴛ ᴀғᴛᴇʀ ʏᴏᴜ ɢᴇᴛ ʟᴏɢɢᴇᴅ ɪɴ!**",
                reply_markup=kb
            )

        except Exception as e:
            await q.answer(f"❌ ᴏᴛᴘ ᴇʀʀᴏʀ: {e}", show_alert=True)
        finally:
            await temp_client.stop()

    # ── Ask logout confirmation ──
    elif data.startswith("ask_log_"):
        s_name = data.replace("ask_log_", "")
        kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("✅ ᴄᴏɴғɪʀᴍ ʟᴏɢᴏᴜᴛ", callback_data=f"done_log_{s_name}")],
            [types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"back_from_logout_{s_name}")]
        ])
        await q.message.edit_text(
            "⚠️ **ʟᴏɢᴏᴜᴛ ʙᴏᴛ ғʀᴏᴍ ᴛʜɪs ᴀᴄᴄᴏᴜɴᴛ?**\n\n"
            "ᴏɴʟʏ ᴄᴏɴғɪʀᴍ ɪғ ʏᴏᴜ ʜᴀᴠᴇ  ᴀʟʀᴇᴅʏ ʟᴏɢɢᴇᴅ ɪɴ ᴏɴ ʏᴏᴜʀ ᴅᴇᴠɪᴄᴇ.",
            reply_markup=kb
        )

    # ── Back from logout ──
    elif data.startswith("back_from_logout_"):
        s_name = data.replace("back_from_logout_", "")
        phone_display = s_name.replace(".session", "")

        conn = get_db()
        cur = conn.cursor()
        order = cur.execute(
            "SELECT country, password, last_otp FROM orders WHERE user_id = ? AND session_name = ?",
            (uid, s_name)
        ).fetchone()
        conn.close()

        if not order:
            return await q.answer("ᴏʀᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!", show_alert=True)

        country, password, last_otp = order
        kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("🔄 ʀᴇғʀᴇsʜ ᴏᴛᴘ", callback_data=f"get_{s_name}")],
            [types.InlineKeyboardButton("🚪 ʟᴏɢᴏᴜᴛ ғʀᴏᴍ ʙᴏᴛ", callback_data=f"ask_log_{s_name}")]
        ])
        await q.message.edit_text(
            f"✅ **ᴏʀᴅᴇʀ ᴀᴄᴛɪᴠᴇ**\n\n"
            f"📞 **ᴘʜᴏɴᴇ:** `{phone_display}`\n"
            f"🌍 **ᴄᴏᴜɴᴛʀʏ:** {country}\n"
            f"🔑 **ᴏᴛᴘ:** `{last_otp}`\n"
            f"🔐 **2ғᴀ:** `{password}`\n\n"
            f"⚠️ **ᴏɴʟʏ ᴄᴏɴғɪʀᴍ ɪғ ʏᴏᴜ ʜᴀᴠᴇ  ᴀʟʀᴇᴅʏ ʟᴏɢɢᴇᴅ ɪɴ ᴏɴ ʏᴏᴜʀ ᴅᴇᴠɪᴄᴇ!**",
            reply_markup=kb
        )

    # ── Done logout ──
    elif data.startswith("done_log_"):
        s_name = data.replace("done_log_", "")
        full_path = ""
        for r, _, f in os.walk(BASE_SESSION_DIR):
            if s_name in f:
                full_path = os.path.join(r, s_name).replace(".session", "")
                break

        if full_path and os.path.exists(f"{full_path}.session"):
            try:
                async with Client(full_path, API_ID, API_HASH) as user_bot:
                    await user_bot.log_out()
                if os.path.exists(f"{full_path}.session"):
                    os.remove(f"{full_path}.session")

                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE orders SET status = 1 WHERE user_id = ? AND session_name = ?",
                    (uid, s_name))
                order = cur.execute(
                    "SELECT country, password FROM orders WHERE user_id = ? AND session_name = ?",
                    (uid, s_name)
                ).fetchone()
                conn.commit()
                conn.close()

                if order:
                    country, password = order
                    phone = s_name.replace(".session", "")
                    await q.message.edit_text(
                        f"✅ **ʙᴏᴛ ʟᴏɢɢᴇᴅ ᴏᴜᴛ!**\n\n"
                        f"📞 **ᴘʜᴏɴᴇ:** `{phone}`\n"
                        f"🌍 **ᴄᴏᴜɴᴛʀʏ:** {country}\n"
                        f"🔐 **2ғᴀ:** `{password}`"
                    )
                else:
                    await q.message.edit_text("✅ **ʙᴏᴛ ʟᴏɢɢᴇᴅ ᴏᴜᴛ!**\n\n🔐 **2ғᴀ:** `nikitayt7`")

            except Exception as e:
                await q.answer(f"❌ ʟᴏɢᴏᴜᴛ ғᴀɪʟᴇᴅ: {e}", show_alert=True)

    # ── User history ──
    elif data == "user_history":
        conn = get_db()
        cur = conn.cursor()
        orders = cur.execute(
            "SELECT session_name, country, price FROM orders WHERE user_id=? ORDER BY timestamp DESC LIMIT 10",
            (uid,)).fetchall()
        conn.close()
        if not orders:
            return await q.answer("ɴᴏ ʜɪsᴛᴏʀʏ!", show_alert=True)
        text = "**📋 ᴘᴜʀᴄʜᴀsᴇ ʜɪsᴛᴏʀʏ**\n\n" + \
            "\n".join(f"📞 `{o[0].replace('.session', '')}` | 🌍 {o[1]} | ₹{o[2]}" for o in orders)
        await q.message.edit_text(
            text,
            reply_markup=types.InlineKeyboardMarkup([[
                types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back_to_stats")
            ]])
        )

    # ── Back to stats ──
    elif data == "back_to_stats":
        bal, spent, dep = get_user_data(uid)
        conn = get_db()
        cur = conn.cursor()
        count = cur.execute(
            "SELECT COUNT(*) FROM orders WHERE user_id=?", (uid,)).fetchone()[0]
        conn.close()
        await q.message.edit_text(
            f"**📊 ʏᴏᴜʀ sᴛᴀᴛɪsᴛɪᴄs**\n\n"
            f"✅ **ᴀᴄᴄᴏᴜɴᴛs ʙᴏᴜɢʜᴛ:** `{count}`\n"
            f"💰 **ᴛᴏᴛᴀʟ sᴘᴇɴᴛ:** `₹{spent:.2f}`\n"
            f"📥 **ᴛᴏᴛᴀʟ ᴅᴇᴘᴏsɪᴛᴇᴅ:** `₹{dep:.2f}`",
            reply_markup=types.InlineKeyboardMarkup([[
                types.InlineKeyboardButton("📋 ᴘᴜʀᴄʜᴀsᴇ ʜɪsᴛᴏʀʏ", callback_data="user_history")
            ]])
        )

    # ── Admin actions ──
    elif data.startswith("adm_"):
        if uid != ADMIN_ID:
            return await q.answer("❌ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ ʙɪᴛᴄʜ⚡", show_alert=True)

        action = data.replace("adm_", "")

        if action == "stats":
            conn = get_db()
            cur = conn.cursor()
            users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            sold = cur.execute("SELECT value FROM business_stats WHERE key='total_sold'").fetchone()[0] or 0
            rev = cur.execute("SELECT value FROM business_stats WHERE key='total_revenue'").fetchone()[0] or 0
            dep = cur.execute("SELECT value FROM business_stats WHERE key='total_deposited'").fetchone()[0] or 0
            conn.close()
            await q.message.edit_text(
                f"**📊 ᴀᴅᴍɪɴ sᴛᴀᴛɪsᴛɪᴄs**\n\n"
                f"👥 **ᴜsᴇʀs:** `{users}`\n"
                f"✅ **sᴏʟᴅ:** `{int(sold)}`\n"
                f"💰 **ʀᴇᴠᴇɴᴜᴇ:** `₹{float(rev):.2f}`\n"
                f"📥 **ᴅᴇᴘᴏsɪᴛs:** `₹{float(dep):.2f}`",
                reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="adm_back")
                ]])
            )

        elif action == "manage_numbers":
            countries = [d for d in os.listdir(BASE_SESSION_DIR) if os.path.isdir(os.path.join(BASE_SESSION_DIR, d))]
            if not countries:
                return await q.message.edit_text("❌ **ɴᴏ ᴄᴏᴜɴᴛɪᴇs ᴀᴠᴀɪʟᴀʙᴇʟ!**")
            buttons = [[types.InlineKeyboardButton(c, callback_data=f"man_country_{c}")] for c in countries]
            buttons.append([types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="adm_back")])
            await q.message.edit_text(
                "**🌍 sᴇʟᴇᴄᴛ ᴀ ᴄᴏᴜɴᴛʀʏ ᴛᴏ ᴍᴀɴᴀɢᴇᴅ:**",
                reply_markup=types.InlineKeyboardMarkup(buttons)
            )

        elif action == "addbal_init":
            login_data[uid] = {"step": "adm_get_id"}
            await q.message.edit_text(
                "**ᴇɴᴛᴇʀ ᴜsᴇʀ ɪᴅ ᴛᴏ ᴀᴅᴅ ʙᴀʟᴀɴᴄᴇ:**",
                reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton("❌ ᴄᴀɴᴄʟᴇ", callback_data="adm_back")
                ]])
            )

        elif action == "addacc":
            login_data[uid] = {"step": "country"}
            await q.message.edit_text("**🌍 ᴇɴᴛᴇʀ ᴄᴏᴜɴᴛʀʏ ɴᴀᴍᴇ (e.g. India):**")

        elif action == "setprice":
            login_data[uid] = {"step": "setprice"}
            await q.message.edit_text("**💲 ᴇɴᴛᴇʀ ɴᴇᴡ ᴅᴇғᴀᴜʟᴛ ᴘʀɪᴄᴇ:**")

        elif action == "country_price":
            login_data[uid] = {"step": "set_country_name"}
            await q.message.edit_text("**🌍 ᴇɴᴛᴇʀ ᴄᴏᴜɴᴛʀʏ ɴᴀᴍᴇ ᴛᴏ sᴇᴛ ᴘʀɪᴄᴇ:**")

        elif action == "broadcast_init":
            login_data[uid] = {"step": "broadcast_msg"}
            await q.message.edit_text(
                "**📢 sᴇɴᴅ ʙʀɪᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ:**",
                reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton("❌ ᴄᴀɴᴄᴋᴇ", callback_data="adm_back")
                ]])
            )

        elif action == "back":
            price = get_setting("price")
            kb = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton(f"💲 ᴅᴇғᴀᴜʟᴛ ᴘʀɪᴄᴇ | ₹{price}", callback_data="adm_setprice")],
                [types.InlineKeyboardButton("➕ ᴀᴅᴅ ʙᴀʟᴀɴᴄᴇ", callback_data="adm_addbal_init")],
                [
                    types.InlineKeyboardButton("📊 sᴛᴀᴛs", callback_data="adm_stats"),
                    types.InlineKeyboardButton("➕ ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ", callback_data="adm_addacc")
                ],
                [types.InlineKeyboardButton("🌍 sᴇᴛ ᴄᴏᴜɴᴛʀʏ ᴘʀɪᴄᴇ", callback_data="adm_country_price")],
                [types.InlineKeyboardButton("📢 ʙʀᴏᴀᴅᴄᴀsᴛ", callback_data="adm_broadcast_init")],
                [types.InlineKeyboardButton("🔢 ᴍᴀɴᴀɢᴇ ɴᴜᴍʙᴇʀs", callback_data="adm_manage_numbers")]
            ])
            await q.message.edit_text("**🔧 ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ**", reply_markup=kb)

    # ── Manage country ──
    elif data.startswith("man_country_"):
        country = data.replace("man_country_", "")
        c_path = os.path.join(BASE_SESSION_DIR, country)
        if not os.path.exists(c_path):
            return await q.message.edit_text("❌ **ғᴏʟᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!**")
        sessions = [f for f in os.listdir(c_path) if f.endswith(".session")]
        if not sessions:
            return await q.message.edit_text(f"❌ **ɴᴏ ɴᴜᴍʙᴇʀs ɪɴ {country}**")
        buttons = [
            [types.InlineKeyboardButton(
                s.replace(".session", ""),
                callback_data=f"man_number_{country}_{s.replace('.session', '')}"
            )] for s in sessions
        ]
        buttons.append([types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="adm_manage_numbers")])
        await q.message.edit_text(
            f"**🔢 sᴇʟᴇᴄᴛ ɴᴜᴍʙᴇʀ ɪɴ{country}:**",
            reply_markup=types.InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("man_number_"):
        parts = data.split("_")
        if len(parts) < 4:
            return await q.answer("Invalid Data!", show_alert=True)
        country = parts[2]
        number = parts[3]
        kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("✅ ʏᴇs ʟᴏɢᴏᴜᴛ", callback_data=f"logout_yes_{country}_{number}")],
            [types.InlineKeyboardButton("❌ ɴᴏ", callback_data=f"logout_no_{country}_{number}")]
        ])
        await q.message.edit_text(
            f"**ᴄᴏɴғɪʀᴍ ʟᴏɢᴏᴜᴛ** `{number}` **in {country}?**",
            reply_markup=kb
        )

    elif data.startswith("logout_no_"):
        parts = data.split("_")
        if len(parts) < 4:
            return await q.answer("Invalid Data!", show_alert=True)
        country = parts[2]
        c_path = os.path.join(BASE_SESSION_DIR, country)
        if not os.path.exists(c_path):
            return await q.message.edit_text("❌ **ғᴏʟᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!**")
        sessions = [f for f in os.listdir(c_path) if f.endswith(".session")]
        if not sessions:
            return await q.message.edit_text(f"❌ **ɴᴏ ɴᴜᴍʙᴇʀs ɪɴ {country}**")
        buttons = [
            [types.InlineKeyboardButton(
                s.replace(".session", ""),
                callback_data=f"man_number_{country}_{s.replace('.session', '')}"
            )] for s in sessions
        ]
        buttons.append([types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="adm_manage_numbers")])
        await q.message.edit_text(
            f"**🔢 sᴇʟᴇᴄʀ ɴᴜᴍʙᴇʀ ɪɴ {country}:**",
            reply_markup=types.InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("logout_yes_"):
        parts = data.split("_")
        if len(parts) < 4:
            return await q.answer("Invalid Data!", show_alert=True)
        country = parts[2]
        number = parts[3]
        full_path = os.path.join(BASE_SESSION_DIR, country, f"{number}.session")
        try:
            if os.path.exists(full_path):
                async with Client(number, API_ID, API_HASH, workdir=os.path.join(BASE_SESSION_DIR, country), no_updates=True) as user_bot:
                    await user_bot.log_out()
        except Exception:
            pass
        if os.path.exists(full_path):
            os.remove(full_path)
        await q.message.edit_text("✅ **ɴᴜᴍʙᴇʀ ʟᴏɢɢᴇᴅ ᴏᴜᴛ ᴀɴᴅ ᴅᴇʟᴇᴛᴇᴅ!**")



# --- /add COMMAND (ADMIN MANUAL BALANCE) ---

@bot.on_message(filters.command("add") & filters.private)
async def add_balance_cmd(c, m):
    if m.from_user.id != ADMIN_ID:
        return await m.reply("❌ **ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ.**")
    args = m.text.split()
    if len(args) != 3:
        return await m.reply("**ᴜsᴀɢᴇ:** `/add {userid} {amount}`\n**Example:** `/add 123456789 500`")
    try:
        target_id = int(args[1])
        amount = float(args[2])
    except ValueError:
        return await m.reply("❌ **ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ ᴏʀ ᴀᴍᴏᴜɴᴛ.**")

    get_user_data(target_id)  # ensure user exists in db
    update_user_stats(target_id, balance_delta=amount, deposit_delta=amount)
    update_biz_stats("total_deposited", amount)
    await m.reply(f"✅ **₹{int(amount)} ᴀᴅᴅᴇᴅ ᴛᴏ** `{target_id}`")
    try:
        await bot.send_message(
            target_id,
            f"🎉 **ʙᴀʟᴀɴᴄᴇ ᴀᴅᴅᴇᴅ!**\n\n"
            f"✅ `₹{int(amount)}` **ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ.**\n"
            f"💰 **ᴜsᴇ /start ᴛᴏ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ.**"
        )
    except BaseException:
        await m.reply(f"⚠️ **ʙᴀʟᴀɴᴄᴇ ᴀᴅᴅᴇᴅ ʙᴜᴛ ᴄᴏᴜʟᴅɴᴛ ɴᴏᴛɪғʏ ᴜsᴇʀ** `{target_id}`")


# --- TEXT / PHOTO INPUT HANDLER ---

@bot.on_message((filters.text | filters.photo) & filters.private)
async def handle_inputs(c, m):
    uid = m.from_user.id
    if uid not in login_data:
        return
    state = login_data[uid]
    text = m.text.strip() if m.text else ""

    # ===== DEPOSIT FLOW =====

    # Step 1: Screenshot
    if state.get("step") == "dep_wait_ss":
        if not m.photo:
            return await m.reply("❌ **ᴘʟs sᴇᴅɴ ᴀ ᴘʜᴏᴛᴏ (screenshot) ᴏғ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ!**")
        state["ss_file_id"] = m.photo.file_id
        state["step"] = "dep_wait_amount"
        await m.reply(
            "✅ **sᴄʀᴇᴇɴsʜᴏᴛ ʀᴇᴄɪᴠᴇᴅ!**\n\n"
            "💰 **ʜᴏᴡ ᴍᴜᴄʜ ᴅɪᴅ ʏᴏᴜ ᴘᴀʏ? sᴇɴᴅ ᴀᴍᴏᴜɴᴛ ɪɴ ɴᴜᴍʙᴇʀs:**\n"
            "Example: `500`"
        )
        return

    # Step 2: Amount → send to admin
    elif state.get("step") == "dep_wait_amount":
        try:
            amt = float(text)
        except (ValueError, AttributeError):
            return await m.reply("❌ **ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ sᴇɴᴅ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.**\nExample: `500`")

        ss = state["ss_file_id"]
        ref = state["ref"]
        username = f"@{m.from_user.username}" if m.from_user.username else "No username"

        kb = types.InlineKeyboardMarkup([
            [
                types.InlineKeyboardButton("✅ ᴀᴘᴘʀᴏᴠᴇ", callback_data=f"aprv_pay_{uid}_{int(amt)}"),
                types.InlineKeyboardButton("❌ ʀᴇᴊᴇᴄᴛ", callback_data=f"rej_pay_{uid}")
            ]
        ])

        await bot.send_photo(
            ADMIN_ID,
            photo=ss,
            caption=(
                f"🔔 **ɴᴇᴡ ᴅᴇᴘᴏsɪᴛ ʀᴇǫᴜᴇsᴛ**\n\n"
                f"👤 **ɴᴀᴍᴇ:** {m.from_user.first_name}\n"
                f"🆔 **ᴜsᴇʀ ɪᴅ:** `{uid}`\n"
                f"🔗 **ᴜsᴇʀɴᴀᴍᴇ:** {username}\n"
                f"💰 **ᴀᴍᴏᴜɴᴛ:** `₹{int(amt)}`\n"
                f"📝 **ʀᴇғ:** `{ref}`\n\n"
                f"👆 **ᴀᴘᴘʀᴏᴠᴇ → ʏᴏᴜ ᴡɪʟʟ ʙᴇ ᴀsᴋᴇᴅ ʜᴏᴡ ᴍᴜᴄʜ ᴛᴏ ᴀᴅᴅ**"
            ),
            reply_markup=kb
        )

        login_data.pop(uid)
        await m.reply(
            "🚀 **ʀᴇǫᴜᴇsᴛ sᴇɴᴛ ᴛᴏ ᴀᴅᴍɪɴ!**\n"
            "ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ ᴡɪʟʟ ʙᴇ ᴀᴅᴅ ᴀғᴛᴇʀ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ."
        )
        return

    # ===== ADMIN: ENTER AMOUNT TO ADD AFTER APPROVING DEPOSIT =====
    elif uid == ADMIN_ID and state.get("step") == "adm_confirm_amt":
        try:
            amount = float(text)
            target_id = state["target_uid"]
            update_user_stats(target_id, balance_delta=amount, deposit_delta=amount)
            update_biz_stats("total_deposited", amount)
            login_data.pop(uid)
            await m.reply(f"✅ **ᴀᴅᴅᴇᴅ ₹{int(amount)} ᴛᴏ ᴜsᴇʀ** `{target_id}`")
            try:
                await bot.send_message(
                    target_id,
                    f"🎉 **ᴅᴇᴘᴏsɪᴛ ᴀᴘᴘᴛᴏᴠᴇᴅ!**\n\n"
                    f"✅ `₹{int(amount)}` **ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ.**\n"
                    f"ᴜsᴇ /start ᴛᴏ ᴄʜᴇᴋ."
                )
            except BaseException:
                pass
        except (ValueError, AttributeError):
            await m.reply("❌ ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ sᴇɴᴅ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")
        return

    # ===== ADMIN ADD BALANCE (manual) =====
    if state.get("step") == "adm_get_id":
        if not text.isdigit():
            return await m.reply("❌ **ɪɴᴠᴀʟɪᴅ ɪᴅ sᴇɴᴅ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.**")
        state.update({"step": "adm_get_amount", "target_id": int(text)})
        await m.reply(f"👤 **ᴜsᴇʀ ɪᴅ:** `{text}`\n💰 **ᴇɴᴛᴇʀ ᴀᴍᴏᴜɴᴛ ᴛᴏ ᴀᴅᴅ (₹):**")
        return

    elif state.get("step") == "adm_get_amount":
        try:
            amount = float(text)
            target_id = state["target_id"]
            update_user_stats(target_id, balance_delta=amount, deposit_delta=amount)
            update_biz_stats("total_deposited", amount)
            login_data.pop(uid)
            await m.reply(f"✅ **ᴀᴅᴅᴇᴅ** `₹{int(amount)}` **ᴛᴏ** `{target_id}`")
            try:
                await bot.send_message(
                    target_id,
                    f"🎉 **₹{int(amount)} ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ!**"
                )
            except BaseException:
                pass
        except (ValueError, AttributeError):
            await m.reply("❌ **ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ.**")
        return

    # ===== ADMIN SET GLOBAL PRICE =====
    if state.get("step") == "setprice":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE settings SET value = ? WHERE key = 'price'", (text,))
        conn.commit()
        conn.close()
        login_data.pop(uid)
        await m.reply(f"✅ **ᴅᴇғᴀᴜʟᴛ ᴘʀɪᴄᴇ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ** `₹{text}`")
        return

    # ===== ADMIN SET COUNTRY PRICE =====
    elif state.get("step") == "set_country_name" and uid == ADMIN_ID:
        state["country"] = text
        state["step"] = "set_country_price"
        await m.reply(f"💲 **Enter Price For {text}:**")
        return

    elif state.get("step") == "set_country_price" and uid == ADMIN_ID:
        try:
            price = float(text)
            country = state["country"]
            set_country_price(country, price)
            login_data.pop(uid)
            await m.reply(f"✅ **ᴘᴛɪᴄᴇ sᴇᴛ ғᴏʀ {country}:** `₹{price}`")
        except (ValueError, AttributeError):
            await m.reply("❌ **ɪɴᴠᴀʟɪᴅ ᴘʀɪᴄᴇ**")
        return

    # ===== ADMIN ADD ACCOUNT =====
    elif uid == ADMIN_ID:
        if state.get("step") == "country":
            state.update({"country": text, "step": "phone"})
            await m.reply("📲 **sᴇɴᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (e.g. +91XXXXXXXXXX):**")
            return

        elif state.get("step") == "phone":
            phone = text.replace(" ", "")
            os.makedirs(BASE_SESSION_DIR, exist_ok=True)
            session_path = f"{BASE_SESSION_DIR}/{phone}"

            if os.path.exists(f"{session_path}.session-journal"):
                try:
                    os.remove(f"{session_path}.session-journal")
                except BaseException:
                    pass

            temp = Client(
                name=phone,
                api_id=API_ID,
                api_hash=API_HASH,
                device_model="ARU X API",
                workdir=BASE_SESSION_DIR
            )

            try:
                await temp.connect()
                chash = await temp.send_code(phone)
                state.update({
                    "step": "otp",
                    "phone": phone,
                    "hash": chash.phone_code_hash,
                    "client": temp
                })
                await m.reply("📩 **ᴏᴛᴘ sᴇɴᴛ! ᴇɴᴛᴇʀ ᴏᴛᴘ:**")
            except Exception as e:
                await m.reply(f"❌ **ᴇʀʀᴏʀ:** `{e}`")
                try:
                    await temp.disconnect()
                except BaseException:
                    pass
                login_data.pop(uid)
            return

        elif state.get("step") == "otp":
            otp_code = text.replace(" ", "")
            try:
                await state["client"].sign_in(state["phone"], state["hash"], otp_code)
                await finalize_admin_acc(state["client"], uid, state["phone"], state["country"])
                login_data.pop(uid)
            except SessionPasswordNeeded:
                state["step"] = "2fa"
                await m.reply("🔐 ** 2ғᴀ ᴇɴᴀʙʟᴇᴅ ᴘʟs sᴇɴᴅ ᴛʜᴇ ᴘᴀssᴡᴏʀᴅ:**")
            except Exception as e:
                await m.reply(f"❌ **ғᴀɪʟᴇᴅ:** `{e}`")
                try:
                    await state["client"].disconnect()
                except BaseException:
                    pass
                login_data.pop(uid)

        elif state.get("step") == "2fa":
            password_2fa = text
            try:
                await state["client"].check_password(password_2fa)
                await finalize_admin_acc(state["client"], uid, state["phone"], state["country"], password_2fa)
                login_data.pop(uid)
            except Exception as e:
                await m.reply(f"❌ **ᴡʀᴏɴɢ ᴘᴀssᴡᴏʀᴅ:** `{e}`")

    # ===== BROADCAST =====
    if state.get("step") == "broadcast_msg" and uid == ADMIN_ID:
        msg_text = m.text
        conn = get_db()
        cur = conn.cursor()
        users = cur.execute("SELECT id FROM users").fetchall()
        conn.close()

        sent_count = 0
        for user in users:
            try:
                await bot.send_message(user[0], f"**{msg_text}**")
                sent_count += 1
            except BaseException:
                continue

        login_data.pop(uid)
        await m.reply(f"✅ **ʙʀᴏᴀᴅᴄᴀsᴛ sᴇɴᴛ ᴛᴏ** `{sent_count}` **Users.**")


# --- SPAMBOT CHECK ---

async def spambot_check(client, bot, admin_id, phone):
    await client.send_message("SpamBot", "/start")
    await asyncio.sleep(3)

    reply_text = ""
    async for msg in client.get_chat_history("SpamBot", limit=1):
        reply_text = msg.text or ""

    if "no limits are currently applied" in reply_text.lower():
        return True

    await bot.send_message(
        admin_id,
        f"⚠️ **SpamBot Warning!**\n\n"
        f"📞 **Phone:** `{phone}`\n\n"
        f"{reply_text}\n\n"
        f"**Reply:**\n"
        f"`/approve_{phone}` — Continue\n"
        f"`/skip_{phone}` — Skip"
    )
    SPAM_APPROVAL[phone] = None
    return None


# --- FINALIZE ACCOUNT ---

async def finalize_admin_acc(client, admin_id, phone, country, current_pwd=None):
    try:
        await asyncio.sleep(2)

        # SpamBot check
        try:
            try:
                await client.unblock_user("spambot")
            except BaseException:
                pass

            allowed = await spambot_check(client, bot, admin_id, phone)

            if allowed is None:
                while SPAM_APPROVAL.get(phone) is None:
                    await asyncio.sleep(2)
                allowed = SPAM_APPROVAL.pop(phone)

            if not allowed:
                await bot.send_message(admin_id, f"⏭ **Account** `{phone}` **skipped (SpamBot).**")
                await client.disconnect()
                return

        except Exception as e:
            await bot.send_message(admin_id, f"⚠️ **SpamBot Warning** `{phone}`:\n`{e}`")

        # Profile
        try:
            me = await client.get_me()
            await client.update_profile(first_name="ꪹꪖᦔꫝꫀꫀ", last_name="", bio="ᡶꪊꪑ ᩏꪖ᭢ỉ ᧒ꫀకỉ ꪉꫀꫝꫝ ᦋꪗꪊ ꪑꪖỉ ꪑꪖꪊకꪖꪑ ᧒ꪖỉకꪖ ꪉꪖᦔꪖꪶ ᦋꪗꪖ..... ᧒ꪖꪉకꫀ ꪑ")
        except Exception as e:
            await bot.send_message(admin_id, f"⚠️ **Profile Warning** `{phone}`:\n`{e}`")

        # Username
        try:
            if getattr(me, "username", None):
                await client.invoke(functions.account.UpdateUsername(username=""))
        except RPCError as e:
            await bot.send_message(admin_id, f"⚠️ **Username Warning** `{phone}`:\n`{e}`")

        # Privacy
        try:
            await client.invoke(
                functions.account.SetPrivacy(
                    key=raw_types.InputPrivacyKeyPhoneNumber(),
                    rules=[raw_types.InputPrivacyValueDisallowAll()]
                )
            )
            await client.invoke(
                functions.account.SetPrivacy(
                    key=raw_types.InputPrivacyKeyAddedByPhone(),
                    rules=[raw_types.InputPrivacyValueAllowContacts()]
                )
            )
        except Exception as e:
            await bot.send_message(admin_id, f"⚠️ **Privacy Warning** `{phone}`:\n`{e}`")

        # 2FA
        try:
            if current_pwd:
                await client.change_cloud_password(current_password=current_pwd, new_password="nikitayt7")
            else:
                await client.enable_cloud_password(password="nikitayt7", hint="")
        except Exception as e:
            await bot.send_message(admin_id, f"⚠️ **2FA Warning** `{phone}`:\n`{e}`")


        # Contacts
        try:
            contacts = await client.invoke(functions.contacts.GetContacts(hash=0))
            if contacts.users:
                await client.invoke(
                    functions.contacts.DeleteContacts(
                        id=[raw_types.InputUser(user_id=u.id, access_hash=u.access_hash) for u in contacts.users]
                    )
                )
                await client.invoke(functions.contacts.ResetSaved())
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
        except Exception as e:
            await bot.send_message(admin_id, f"⚠️ **Contacts Error** `{phone}`:\n`{e}`")

        # Chat cleanup
        try:
            async for dialog in client.get_dialogs():
                chat = dialog.chat

                if chat.id == 777000:
                    continue
                if getattr(chat, "username", None) and chat.username.lower() == "spambot":
                    continue

                if chat.id == "me":
                    try:
                        peer = await client.resolve_peer("me")
                        await client.invoke(functions.messages.DeleteHistory(peer=peer, max_id=0, revoke=True))
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except BaseException:
                        pass
                    continue

                if chat.type == "bot":
                    try:
                        peer = await client.resolve_peer(chat.id)
                        await client.invoke(functions.messages.DeleteHistory(peer=peer, max_id=0, revoke=True))
                        await client.block_user(chat.id)
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except BaseException:
                        continue

                elif chat.type == "private":
                    try:
                        peer = await client.resolve_peer(chat.id)
                        await client.invoke(functions.messages.DeleteHistory(peer=peer, max_id=0, revoke=True))
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except BaseException:
                        continue

                else:
                    try:
                        await client.leave_chat(chat.id)
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except BaseException:
                        continue

        except Exception as e:
            await bot.send_message(admin_id, f"⚠️ **Chat Cleanup Error** `{phone}`:\n`{e}`")

        # Session move
        try:
            c_path = os.path.join(BASE_SESSION_DIR, country)
            os.makedirs(c_path, exist_ok=True)
            await client.disconnect()
            phone_str = str(phone).strip()
            shutil.move(
                f"{BASE_SESSION_DIR}/{phone_str}.session",
                f"{c_path}/{phone_str}.session"
            )
        except Exception as e:
            await bot.send_message(admin_id, f"⚠️ **Session Move Warning** `{phone}`:\n`{e}`")

        # Success
        await bot.send_message(
            admin_id,
            f"✅ **ᴀᴄᴄᴏᴜɴᴛ ᴀᴅᴅᴇᴅ!**\n\n"
            f"📞 `{phone}`\n"
            f"🌍 **ᴄᴏᴜɴᴛʀʏ:** {country}\n"
            f"✅ **sᴘᴀᴍʙᴏᴛ: ᴄʟᴇᴀɴ**"
        )

    except Exception as e:
        await bot.send_message(admin_id, f"❌ **Fatal Error** `{phone}`:\n`{e}`")


# --- RUN BOT ---
print("Bot is Starting...")
bot.run()
