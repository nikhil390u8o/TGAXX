import os
from pyrogram import Client, filters, types
from pyrogram.errors import SessionPasswordNeeded
from config import ADMIN_ID, API_ID, API_HASH, BASE_SESSION_DIR
from database import (get_db, get_user_data, update_user_stats,
                      update_biz_stats, get_country_price, set_country_price)
from utils import finalize_admin_acc


def register_inputs(bot, login_data):

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
                return await m.reply("❌ **ᴘʟs sᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ (screenshot) ᴏғ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ!**")
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
                "ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ ᴡɪʟʟ ʙᴇ ᴀᴅᴅ ᴀғᴛᴇʀ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ.\n"
                "ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴜʀɢᴇɴᴛʟʏ ᴅᴍ ᴀᴛᴇ @ll_PANDA_BBY_ll."
            )
            return

        # ===== ADMIN: APPROVE DEPOSIT AMOUNT =====
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
                        f"🎉 **ᴅᴇᴘᴏsɪᴛ ᴀᴘᴘʀᴏᴠᴇᴅ!**\n\n"
                        f"✅ `₹{int(amount)}` **ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ.**\n"
                        f"ᴜsᴇ /start ᴛᴏ ᴄʜᴇᴋ."
                    )
                except BaseException:
                    pass
            except (ValueError, AttributeError):
                await m.reply("❌ ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ sᴇɴᴅ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.")
            return

        # ===== ADMIN ADD BALANCE =====
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
                    await bot.send_message(target_id, f"🎉 **₹{int(amount)} ᴀᴅᴅᴇᴅ ᴛᴏ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ!**")
                except BaseException:
                    pass
            except (ValueError, AttributeError):
                await m.reply("❌ **ɪɴᴠᴀʟɪᴅ ᴀᴍᴏᴜɴᴛ.**")
            return

        # ===== ADMIN SET PRICE =====
        if state.get("step") == "setprice":
            conn = get_db()
            cur = conn.cursor()
            cur.execute("UPDATE settings SET value = ? WHERE key = 'price'", (text,))
            conn.commit()
            conn.close()
            login_data.pop(uid)
            await m.reply(f"✅ **ᴅᴇғᴀᴜʟᴛ ᴘʀɪᴄᴇ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ** `₹{text}`")
            return

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
                await m.reply(f"✅ **ᴘʀɪᴄᴇ sᴇᴛ ғᴏʀ {country}:** `₹{price}`")
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
                    await finalize_admin_acc(state["client"], bot, uid, state["phone"], state["country"])
                    login_data.pop(uid)
                except SessionPasswordNeeded:
                    state["step"] = "2fa"
                    await m.reply("🔐 **2ғᴀ ᴇɴᴀʙʟᴇᴅ ᴘʟs sᴇɴᴅ ᴛʜᴇ ᴘᴀssᴡᴏʀᴅ:**")
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
                    await finalize_admin_acc(state["client"], bot, uid, state["phone"], state["country"], password_2fa)
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
