import os
import re
from pyrogram import Client, filters, types
from config import BASE_SESSION_DIR, API_ID, API_HASH, LOG_CHANNEL_ID
from database import get_user_data, get_country_price, get_db, update_user_stats, update_biz_stats


def register_buy(bot):

    @bot.on_message(filters.regex("Buy Account") & filters.private)
    async def buy_acc_start(c, m):
        uid = m.from_user.id

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT session_name FROM orders WHERE user_id = ? AND status = 0", (uid,))
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

    # Expose buy_acc_start so callbacks can call it
    bot._buy_acc_start = buy_acc_start
