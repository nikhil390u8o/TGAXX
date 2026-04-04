from pyrogram import filters, types
from config import ADMIN_ID, SPAM_APPROVAL
from database import get_setting, get_user_data, update_user_stats, update_biz_stats


def register_admin(bot, login_data):

    @bot.on_message(filters.command("admin") & filters.private | filters.group)
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

    @bot.on_message(filters.command("add") & filters.private | filters.group)
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

        get_user_data(target_id)
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

    @bot.on_message(filters.command("approve_") & filters.private | filters.group)
    async def approve_spam(c, m):
        if m.from_user.id != ADMIN_ID:
            return
        phone = m.text.split("_", 1)[1]
        SPAM_APPROVAL[phone] = True
        await m.reply(f"✅ `{phone}` **Approved! Continuing...**")

    @bot.on_message(filters.command("skip_") & filters.private | filters.group)
    async def skip_spam(c, m):
        if m.from_user.id != ADMIN_ID:
            return
        phone = m.text.split("_", 1)[1]
        SPAM_APPROVAL[phone] = False
        await m.reply(f"⏭ `{phone}` **Skipped!**")
