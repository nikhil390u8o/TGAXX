import random
import urllib.parse
from pyrogram import filters, types
from config import ADMIN_ID
from database import update_user_stats, update_biz_stats

login_data = {}


def register_deposit(bot):

    @bot.on_message(filters.regex("Deposit") & filters.private | filters.group)
    async def deposit_init(c, m):
        uid = m.from_user.id

        upi_id = "nikhil-bby@fam"
        ref_id = f"REF{random.randint(1000, 9999)}"

        upi_link = f"upi://pay?pa={upi_id}&pn=TGKing&tn={ref_id}"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={urllib.parse.quote(upi_link)}"

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
