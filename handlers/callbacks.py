import os
import re
from pyrogram import Client, filters, types
from config import (ADMIN_ID, API_ID, API_HASH, BASE_SESSION_DIR,
                    LOG_CHANNEL_ID, WELCOME_IMAGE)
from database import (get_db, get_user_data, get_country_price,
                      get_setting, set_country_price,
                      update_user_stats, update_biz_stats)
from utils import check_force_join


def register_callbacks(bot, login_data):

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
                buttons.append([types.InlineKeyboardButton("𝐕𝐄𝐑𝐈𝐅𝐘", callback_data="verify_join")])
                await q.answer("❌ 𝐉𝐎𝐈𝐍 𝐊𝐀𝐑𝐎 𝐍𝐀 𝐐𝐓 😒!", show_alert=True)
                try:
                    await q.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(buttons))
                except Exception:
                    pass
                return

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
                    "✅ **ʏᴏᴜ ᴀʀᴇ ᴠᴇʀɪғɪᴇᴅ!**"
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

        # ── Admin approves deposit ──
        elif data.startswith("aprv_pay_"):
            parts = data.split("_")
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

            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO orders (user_id, session_name, status, country, price, password) VALUES (?, ?, 0, ?, ?, ?)",
                (uid, s_name, country, price, "nikitayt7")
            )
            conn.commit()
            conn.close()

            half_num = phone_num[:6] + "****" if len(phone_num) >= 6 else phone_num
            kb = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("📩 ɢᴇᴛ ᴏᴛᴘ", callback_data=f"get_{s_name}")]
            ])
            await q.message.edit_text(
                f"✅ **ᴏʀᴅᴇʀ ᴀᴄᴛɪᴠᴇ!**\n\n"
                f"📞 **ᴘʜᴏɴᴇ:** `{phone_num}`\n"
                f"🌍 **ᴄᴏᴜɴᴛʀʏ:** {country}\n\n"
                f"**📋 ɪɴsᴛʀᴜᴄᴛɪᴏɴ:**\n"
                f"1. ᴏᴘᴇɴ ᴛᴇʟᴇɢʀᴀᴍ → ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ\n"
                f"2. ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴜᴍʙᴇʀ\n"
                f"3. ᴄʟɪᴄᴋ **ɢᴇᴛ ᴏᴛᴘ** ᴀғᴛᴇʀ ᴏᴛᴘ ᴀʀʀɪᴠᴇs\n"
                f"4. ᴜsᴇ ɴɪᴄᴇɢʀᴀᴍ ᴏʀ ᴛᴇʟᴇɢʀᴀᴍ x ғᴏʀ sᴀғᴇ ʟᴏɢɪɴ",
                reply_markup=kb
            )

            username = f"@{q.from_user.username}" if q.from_user.username else "No username"
            try:
                await bot.send_message(
                    int(LOG_CHANNEL_ID),
                    f"**ᴀᴄᴄᴏᴜɴᴛ sᴇʟʟᴇᴅ** ✅\n\n"
                    f"**ᴜsᴇʀ** — `{q.from_user.id}` ({username})\n"
                    f"**ᴄᴏᴜɴᴛʀʏ** — {country}\n"
                    f"**ɴᴜᴍʙ** — `{half_num}`\n"
                    f"**ᴘʀɪᴄᴇ** — ₹{price}"
                )
            except Exception:
                pass

        # ── Back to buy ──
        elif data == "back_to_buy":
            await q.message.delete()

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
                    f"⚠️ **ʙᴏᴛ ɪs ᴀʟʀᴇᴀᴅʏ ʟᴏɢɢᴇᴅ ᴏᴜᴛ!**\n\n"
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
                    return await q.answer("❌ ᴏᴛᴘ ɴᴏᴛ ғᴏᴜɴᴅ sᴇɴᴅ ᴏᴛᴘ ғɪʀsᴛ.", show_alert=True)

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
                    [types.InlineKeyboardButton("🔄 ʀᴇғʀᴇsʜ ᴏᴛᴘ", callback_data=f"get_{s_name}")],
                    [types.InlineKeyboardButton("🚪 ʟᴏɢᴏᴜᴛ ʙᴏᴛ", callback_data=f"ask_log_{s_name}")]
                ])
                await q.message.edit_text(
                    f"✅ **ᴏʀᴅᴇʀ ᴄᴏᴍᴘʟᴇᴛᴇ!**\n\n"
                    f"📞 **ᴘʜᴏɴᴇ:** `{phone_display}`\n"
                    f"🌍 **ᴄᴏᴜɴᴛʀʏ:** {country}\n"
                    f"🔑 **ᴏᴛᴘ:** `{otp_found}`\n"
                    f"🔐 **ᴘᴀss:** `{password}`\n\n"
                    f"⚠️ **ᴄʟɪᴄᴋ ʟᴏɢᴏᴜᴛ ᴏɴʟʏ ᴀғᴛᴇʀ ʏᴏᴜ ʜᴀᴠᴇ ʟᴏɢɢᴇᴅ ɪɴ!**",
                    reply_markup=kb
                )
            except Exception as e:
                await q.answer(f"❌ OTP Error: {e}", show_alert=True)
            finally:
                try:
                    await temp_client.stop()
                except Exception:
                    pass

        # ── Ask logout ──
        elif data.startswith("ask_log_"):
            s_name = data.replace("ask_log_", "")
            kb = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("✅ ᴄᴏɴғɪʀᴍ ʟᴏɢᴏᴜᴛ", callback_data=f"done_log_{s_name}")],
                [types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"back_from_logout_{s_name}")]
            ])
            await q.message.edit_text(
                "⚠️ **ʟᴏɢᴏᴜᴛ ʙᴏᴛ ғʀᴏᴍ ᴛʜɪs ᴀᴄᴄᴏᴜɴᴛ?**\n\n"
                "ᴏɴʟʏ ᴄᴏɴғɪʀᴍ ɪғ ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ʟᴏɢɢᴇᴅ ɪɴ.",
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
                return await q.answer("Order Not Found!", show_alert=True)
            country, password, last_otp = order
            kb = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("🔄 ʀᴇғʀᴇsʜ ᴏᴛᴘ", callback_data=f"get_{s_name}")],
                [types.InlineKeyboardButton("🚪 ʟᴏɢᴏᴜᴛ ʙᴏᴛ", callback_data=f"ask_log_{s_name}")]
            ])
            await q.message.edit_text(
                f"✅ **ᴏʀᴅᴇʀ ᴀᴄᴛɪᴠᴇ**\n\n"
                f"📞 **ᴘʜᴏɴᴇ:** `{phone_display}`\n"
                f"🌍 **ᴄᴏᴜɴᴛʀʏ:** {country}\n"
                f"🔑 **ᴏᴛᴘ:** `{last_otp}`\n"
                f"🔐 **ᴘᴀss:** `{password}`",
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
                    cur.execute("UPDATE orders SET status = 1 WHERE user_id = ? AND session_name = ?", (uid, s_name))
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
                            f"🔐 **ᴘᴀss:** `{password}`"
                        )
                    else:
                        await q.message.edit_text("✅ **ʙᴏᴛ ʟᴏɢɢᴇᴅ ᴏᴜᴛ!**")
                except Exception as e:
                    await q.answer(f"❌ Logout Failed: {e}", show_alert=True)

        # ── User history ──
        elif data == "user_history":
            conn = get_db()
            cur = conn.cursor()
            orders = cur.execute(
                "SELECT session_name, country, price FROM orders WHERE user_id=? ORDER BY timestamp DESC LIMIT 10",
                (uid,)).fetchall()
            conn.close()
            if not orders:
                return await q.answer("No History!", show_alert=True)
            text = "**📋 ᴘᴜʀᴄʜᴀsᴇ ʜɪsᴛᴏʀʏ**\n\n" + \
                "\n".join(f"📞 `{o[0].replace('.session', '')}` | 🌍 {o[1]} | ₹{o[2]}" for o in orders)
            await q.message.edit_text(
                text,
                reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back_to_stats")
                ]])
            )

        elif data == "back_to_stats":
            bal, spent, dep = get_user_data(uid)
            conn = get_db()
            cur = conn.cursor()
            count = cur.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (uid,)).fetchone()[0]
            conn.close()
            await q.message.edit_text(
                f"**📊 ʏᴏᴜʀ sᴛᴀᴛɪsᴛɪᴄs**\n\n"
                f"✅ **ᴀᴄᴄᴏᴜɴsᴛ ʙᴏᴜɢʜᴛ:** `{count}`\n"
                f"💰 **ᴛᴏᴛᴀʟ sᴘᴇɴᴛ:** `₹{spent:.2f}`\n"
                f"📥 **ᴛᴏᴛᴀʟ ᴅᴇᴘᴏsɪᴛᴇᴅ:** `₹{dep:.2f}`",
                reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton("📋 ᴠɪᴇᴡ ʜɪsᴛᴏʀʏ", callback_data="user_history")
                ]])
            )

        # ── Admin actions ──
        elif data.startswith("adm_"):
            if uid != ADMIN_ID:
                return await q.answer("❌ Unauthorized", show_alert=True)
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
                import os
                countries = [d for d in os.listdir(BASE_SESSION_DIR) if os.path.isdir(os.path.join(BASE_SESSION_DIR, d))]
                if not countries:
                    return await q.message.edit_text("❌ **ɴᴏ ᴄᴏᴜɴᴛʀɪᴇs ᴀᴠᴀɪʟᴀʙʟᴇ!**")
                buttons = [[types.InlineKeyboardButton(c, callback_data=f"man_country_{c}")] for c in countries]
                buttons.append([types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="adm_back")])
                await q.message.edit_text("**🌍 sᴇʟᴇᴄᴛ ᴀ ᴄᴏᴜɴᴛʀʏ ᴛᴏ ᴍᴀɴᴀɢᴇ:**", reply_markup=types.InlineKeyboardMarkup(buttons))

            elif action == "addbal_init":
                login_data[uid] = {"step": "adm_get_id"}
                await q.message.edit_text(
                    "**ᴇɴᴛᴇʀ ᴜsᴇʀ ɪᴅ ᴛᴏ ᴀᴅᴅ ʙᴀʟᴀɴᴄᴇ:**",
                    reply_markup=types.InlineKeyboardMarkup([[types.InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="adm_back")]])
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
                    "**📢 sᴇɴᴅ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ:**",
                    reply_markup=types.InlineKeyboardMarkup([[types.InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="adm_back")]])
                )

            elif action == "back":
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
                await q.message.edit_text("**🔧 ᴀᴅᴍɪɴ.ᴘᴀɴᴇʟ**", reply_markup=kb)

        # ── Manage country/numbers ──
        elif data.startswith("man_country_"):
            country = data.replace("man_country_", "")
            c_path = os.path.join(BASE_SESSION_DIR, country)
            if not os.path.exists(c_path):
                return await q.message.edit_text("**❌ ғᴏʟᴅᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!**")
            sessions = [f for f in os.listdir(c_path) if f.endswith(".session")]
            if not sessions:
                return await q.message.edit_text(f"❌ **ɴᴏ ɴᴜᴍʙᴇʀs ɪɴ {country}**")
            buttons = [
                [types.InlineKeyboardButton(s.replace(".session", ""), callback_data=f"man_number_{country}_{s.replace('.session', '')}")]
                for s in sessions
            ]
            buttons.append([types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="adm_manage_numbers")])
            await q.message.edit_text(f"**🔢 sᴇʟᴇᴄᴛ ɴᴜᴍʙᴇʀ ɪɴ {country}:**", reply_markup=types.InlineKeyboardMarkup(buttons))

        elif data.startswith("man_number_"):
            parts = data.split("_")
            if len(parts) < 4:
                return await q.answer("Invalid Data!", show_alert=True)
            country, number = parts[2], parts[3]
            kb = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("✅ ʏᴇs ʟᴏɢᴏᴜᴛ", callback_data=f"logout_yes_{country}_{number}")],
                [types.InlineKeyboardButton("❌ ɴᴏ", callback_data=f"logout_no_{country}_{number}")]
            ])
            await q.message.edit_text(f"**ᴄᴏɴғɪʀᴍ ʟᴏɢᴏᴜᴛ ғᴏʀ** `{number}` **ɪɴ {country}?**", reply_markup=kb)

        elif data.startswith("logout_yes_"):
            parts = data.split("_")
            if len(parts) < 4:
                return await q.answer("Invalid Data!", show_alert=True)
            country, number = parts[2], parts[3]
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

        elif data.startswith("logout_no_"):
            parts = data.split("_")
            if len(parts) < 4:
                return await q.answer("Invalid Data!", show_alert=True)
            country = parts[2]
            c_path = os.path.join(BASE_SESSION_DIR, country)
            sessions = [f for f in os.listdir(c_path) if f.endswith(".session")]
            buttons = [
                [types.InlineKeyboardButton(s.replace(".session", ""), callback_data=f"man_number_{country}_{s.replace('.session', '')}")]
                for s in sessions
            ]
            buttons.append([types.InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="adm_manage_numbers")])
            await q.message.edit_text(f"**🔢 sᴇʟᴇᴄᴛ ɴᴜᴍʙᴇʀ ɪɴ {country}:**", reply_markup=types.InlineKeyboardMarkup(buttons))
