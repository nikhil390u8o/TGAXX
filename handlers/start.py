from pyrogram import filters, types
from config import WELCOME_IMAGE, FORCE_JOIN_CHANNELS
from database import get_user_data
from utils import check_force_join


def register_start(bot):

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

    @bot.on_message(filters.regex("Profile") & filters.private)
    async def profile_h(c, m):
        uid = m.from_user.id
        data = get_user_data(uid)
        await m.reply(
            f"👤 **ɴᴀᴍᴇ:** {m.from_user.first_name}\n"
            f"🆔 **ᴜsᴇʀ ɪᴅ:** `{uid}`\n"
            f"💰 **ʙᴀʟᴀɴᴄᴇ:** `₹{data[0]:.2f}`"
        )

    @bot.on_message(filters.regex("My Stats") & filters.private)
    async def user_stats_h(c, m):
        from database import get_db
        uid = m.from_user.id
        bal, spent, dep = get_user_data(uid)
        conn = get_db()
        cur = conn.cursor()
        count = cur.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (uid,)).fetchone()[0]
        conn.close()
        text = (
            f"**📊 ʏᴏᴜʀ sᴛᴀᴛɪsᴛɪᴄs**\n\n"
            f"✅ **ᴀᴄᴄᴏᴜɴsᴛ ʙᴏᴜɢʜᴛ:** `{count}`\n"
            f"💰 **ᴛᴏᴛᴀʟ sᴘᴇɴᴛ:** `₹{spent:.2f}`\n"
            f"📥 **ᴛᴏᴛᴀʟ ᴅᴇᴘᴏsɪᴛᴇᴅ:** `₹{dep:.2f}`"
        )
        kb = types.InlineKeyboardMarkup([[
            types.InlineKeyboardButton("📋 ᴠɪᴇᴡ ʜɪsᴛᴏʀʏ", callback_data="user_history")
        ]])
        await m.reply(text, reply_markup=kb)
