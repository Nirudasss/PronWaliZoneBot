import os
from pyrogram import Client, filters
from pyrogram.types import Message
from database.users_db import db
from info import ADMINS
from plugins.ban_manager import ban_manager

# ==================================================================
# 🚫 BAN USER
# ==================================================================
@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_user_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "⚠ **Usage:**\n`/ban user_id`\n`/ban user_id reason`",
            quote=True
        )
    try:
        user_id = int(message.command[1])
        reason = " ".join(message.command[2:]) if len(message.command) > 2 else "Admin Ban"
    except ValueError:
        return await message.reply("❌ **Invalid User ID.**", quote=True)
    # 🔐 Admin safety
    if (isinstance(ADMINS, list) and user_id in ADMINS) or user_id == ADMINS:
        return await message.reply("❌ **You cannot ban an Admin!**", quote=True)
    try:
        await db.block_user(user_id, reason)
        ban_manager.blocked_cache[user_id] = True
        await message.reply(
            f"✅ **User Banned!**\n\n🆔 `{user_id}`\n📝 `{reason}`",
            quote=True
        )
        try:
            await client.send_message(
                user_id,
                f"🚫 <b> 𝘠𝘰𝘶 𝘩𝘢𝘷𝘦 𝘣𝘦𝘦𝘯 𝘣𝘢𝘯𝘯𝘦𝘥 𝘧𝘳𝘰𝘮 𝘶𝘴𝘪𝘯𝘨 𝘵𝘩𝘪𝘴 𝘣𝘰𝘵 </b>\n\n{reason}"
            )
        except:
            pass
    except Exception as e:
        await message.reply(f"❌ Error banning user: `{e}`", quote=True)


# ==================================================================
# ✅ UNBAN USER
# ==================================================================
@Client.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban_user_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("⚠ **Usage:**\n`/unban user_id`", quote=True)
    try:
        user_id = int(message.command[1])
    except ValueError:
        return await message.reply("❌ **Invalid User ID.**", quote=True)
    try:
        await db.unblock_user(user_id)
        ban_manager.blocked_cache[user_id] = False
        ban_manager.user_flood_history.pop(user_id, None)
        ban_manager.user_warnings.pop(user_id, None)
        await message.reply(
            f"✅ **User Unbanned!**\n\n🆔 `{user_id}`",
            quote=True
        )
        try:
            await client.send_message(
                user_id,
                "✅ 𝘠𝘰𝘶 𝘩𝘢𝘷𝘦 𝘣𝘦𝘦𝘯 𝘶𝘯𝘣𝘢𝘯𝘯𝘦𝘥 𝘢𝘯𝘥 𝘤𝘢𝘯 𝘯𝘰𝘸 𝘶𝘴𝘦 𝘵𝘩𝘦 𝘣𝘰𝘵 𝘢𝘨𝘢𝘪𝘯."
            )
        except:
            pass
    except Exception as e:
        await message.reply(f"❌ Error unbanning user: `{e}`", quote=True)


# ==================================================================
# 📜 LIST BLOCKED USERS
# ==================================================================
@Client.on_message(filters.command("blocked") & filters.user(ADMINS))
async def list_blocked_users(client, message: Message):
    status_msg = await message.reply("🔄 **Fetching blocked users...**")
    blocked_list = []
    cursor = await db.get_all_blocked_users()
    async for user in cursor:
        blocked_list.append(user)
    if not blocked_list:
        return await status_msg.edit("✅ **No blocked users found.**")
    if len(blocked_list) > 20:
        file_path = "Blocked_Users_List.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("🚫 BLOCKED USERS LIST\n")
            f.write("=====================\n\n")
            for user in blocked_list:
                f.write(f"ID: {user['user_id']}\n")
                f.write(f"Reason: {user.get('reason','N/A')}\n")
                f.write("---------------------\n")
        await message.reply_document(
            document=file_path,
            caption=f"🚫 **Total Blocked Users:** `{len(blocked_list)}`"
        )
        if os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()
    else:
        text = "**🚫 Blocked Users List:**\n\n"
        for user in blocked_list:
            text += f"• `{user['user_id']}` | _{user.get('reason','N/A')}_\n"
        await status_msg.edit(text)


