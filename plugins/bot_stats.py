import os
import pytz
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import *
from database.users_db import db
from info import ADMINS, PREMIUM_DAILY_LIMIT, DAILY_LIMIT
from utils import get_size
from Script import script

# ---------------------------------------------------------------------------------
# 📊 BOT STATISTICS COMMAND
# ---------------------------------------------------------------------------------
@Client.on_message(filters.command('stats') & filters.user(ADMINS) & filters.incoming)
async def get_stats(bot, message: Message):
    aVBOTz = await message.reply("🔄 **Fetching stats...**")
    total_users = await db.total_users_count()
    premium_users = await db.premium_users_count()
    mixfiles = await db.total_files_count()
    brazzers = await db.total_brazzers_videos()
    blocked = await db.total_blocked_count()
    redeem = await db.total_redeem_count()
    dbsize = await db.get_db_size()
    freespace = 536870912 - dbsize 
    try:
        db_size_human = get_size(dbsize)
        free_space_human = get_size(freespace)
    except:
        db_size_human = await get_size(dbsize)
        free_space_human = await get_size(freespace)
    try:
        await aVBOTz.edit(script.STATS_TXT.format(
            total_users=total_users,
            premium_users=premium_users,
            redeem=redeem,
            blocked=blocked,
            mixfiles=mixfiles,
            brazzers=brazzers,
            db_size_human=db_size_human,
            free_space_human=free_space_human
        ))
    except Exception as e:
        await aVBOTz.edit(f"❌ **Error in Stats Format:** {e}")

# ---------------------------------------------------------------------------------
# 🗑 DELETE ALL FILES COMMAND
# ---------------------------------------------------------------------------------
@Client.on_message(filters.command("deleteall") & filters.user(ADMINS))
async def delete_command_handler(client, message):
    # Buttons banate hain selection ke liye
    buttons = [
        [
            InlineKeyboardButton("🗑 Delete Main Videos", callback_data="del_ask_main"),
            InlineKeyboardButton("🔞 Delete Brazzers", callback_data="del_ask_brazzers")
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="del_cancel")
        ]
    ]
    
    await message.reply(
        "**⚠️ WARNING: DELETION MENU**\n\n"
        "Aap kaunsa database clear karna chahte hain?\n"
        "Select karne ke baad confirmation mangunga.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# --- Callback Query Handler (Button Click Handle karne ke liye) ---
@Client.on_callback_query(filters.regex(r"^del_"))
async def delete_callback_handler(client, callback: CallbackQuery):
    data = callback.data
    
    # 1. Cancel logic
    if data == "del_cancel":
        await callback.message.delete()
        return

    # 2. Confirmation Logic (User ne select kiya, ab confirm karega)
    if data == "del_ask_main":
        await callback.message.edit(
            "⚠️ **CONFIRMATION: MAIN VIDEOS**\n\n"
            "Kya aap sach mein **Main Videos & History** delete karna chahte hain?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, Delete Main", callback_data="del_confirm_main")],
                [InlineKeyboardButton("❌ No, Cancel", callback_data="del_cancel")]
            ])
        )
    
    elif data == "del_ask_brazzers":
        await callback.message.edit(
            "⚠️ **CONFIRMATION: BRAZZERS**\n\n"
            "Kya aap sach mein **Brazzers Videos & History** delete karna chahte hain?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, Delete Brazzers", callback_data="del_confirm_brazzers")],
                [InlineKeyboardButton("❌ No, Cancel", callback_data="del_cancel")]
            ])
        )

    # 3. Execution Logic (Database se delete karna)
    elif data == "del_confirm_main":
        await callback.message.edit("⏳ **Deleting Main Videos... Please wait.**")
        try:
            await db.delete_main_data() # Database function call
            await callback.message.edit("✅ **Successfully deleted ALL Main Videos and History!**")
        except Exception as e:
            await callback.message.edit(f"❌ Error: {e}")

    elif data == "del_confirm_brazzers":
        await callback.message.edit("⏳ **Deleting Brazzers Data... Please wait.**")
        try:
            await db.delete_brazzers_data() # Database function call
            await callback.message.edit("✅ **Successfully deleted ALL Brazzers Videos and History!**")
        except Exception as e:
            await callback.message.edit(f"❌ Error: {e}")
            

# ---------------------------------------------------------------------------------
# 📈 ACTIVE USERS REPORT COMMAND
# ---------------------------------------------------------------------------------
@Client.on_message(filters.command("all_users_stats") & filters.user(ADMINS) & filters.incoming)
async def all_users_stats(client, message: Message):
    status_msg = await message.reply("🔄 **Fetching active users stats... Please wait.**")
    users_cursor = db.users.find({}) 
    report_list = [] 
    total_files_used = 0
    active_users_count = 0 
    async for user in users_cursor:
        user_id = user.get("id", "N/A")
        username = user.get("username")
        username_display = f"@{username}" if username else "N/A"
        used = await db.get_video_count(user_id)
        if used == 0:
            continue
        is_premium = await db.has_premium_access(user_id)
        daily_limit = PREMIUM_DAILY_LIMIT if is_premium else DAILY_LIMIT
        remaining = max(daily_limit - used, 0)
        total_files_used += used
        subscription_type = "Paid" if is_premium else "Free"
        user_entry = (
            f"👤 User: {username_display} ({user_id})\n"
            f"╰ 💠 Plan: {subscription_type}\n"
            f"╰ 📁 Daily Limit: {daily_limit} | Used: {used} | Remaining: {remaining}"
        )
        expiry_time = user.get("expiry_time")
        if is_premium and expiry_time:
            try:
                if isinstance(expiry_time, datetime):
                    expiry_dt = expiry_time.astimezone(pytz.timezone("Asia/Kolkata"))
                    expiry_date = expiry_dt.strftime('%d-%m-%Y')
                    expiry_clock = expiry_dt.strftime('%I:%M:%S %p')
                    user_entry += f"\n╰ 🗓 Expiry: {expiry_date} at {expiry_clock}"
            except Exception as e:
                print(f"Expiry date parse error for user {user_id}: {e}")
        report_list.append(user_entry)
        active_users_count += 1
    summary_text = (
        f"🧾 Active Users (>=1 download): {active_users_count}\n"
        f"📊 Total Files Used: {total_files_used}"
    )
    if active_users_count > 10:
        file_path = f"Active_Users_Stats.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("📊 ACTIVE USERS PLAN STATS REPORT\n")
            f.write("=================================\n\n")
            f.write("\n\n---------------------------------\n\n".join(report_list))
            f.write("\n\n=================================\n")
            f.write(summary_text)
        await message.reply_document(
            document=file_path,
            caption=(
                f"📊 **Active Users Report Generated**\n\n"
                f"🧾 **Active Users:** `{active_users_count}`\n"
                f"📂 **Total Usage:** `{total_files_used}`\n\n"
                f"ℹ️ _List is sent as a file because there are more than 10 active users._"
            )
        )
        if os.path.exists(file_path):
            os.remove(file_path)

    else:
        if active_users_count == 0:
            final_msg = "❌ No active users found (Usage = 0)."
        else:
            formatted_entries = []
            for entry in report_list:
                entry = entry.replace("User:", "**User:**").replace("Plan:", "`Plan:`")
                formatted_entries.append(entry)
            final_msg = "**📊 Active Users Plan Stats:**\n\n" + "\n\n".join(formatted_entries) + "\n\n" + f"**{summary_text}**"
        if len(final_msg) > 4096:
             # Fallback if text > 4096 chars but < 10 users
             with open("Stats.txt", "w", encoding="utf-8") as f:
                 f.write(final_msg.replace("**", "").replace("`", ""))
             await message.reply_document("Stats.txt")
             if os.path.exists("Stats.txt"):
                 os.remove("Stats.txt")
        else:
            await message.reply(final_msg)
    await status_msg.delete()

# ---------------------------------------------------------------------------------
# 🔍 CHECK SPECIFIC USER COMMAND
# ---------------------------------------------------------------------------------
@Client.on_message(filters.command("check_user") & filters.user(ADMINS) & filters.incoming)
async def check_user_handler(client, message: Message):
    if len(message.command) != 2:
        return await message.reply("❗ Usage: `/check_user user_id`", quote=True)
    try:
        user_id = int(message.command[1])
    except ValueError:
        return await message.reply("❌ Invalid User ID. Please enter a valid number.")
    user = await db.get_user(user_id)
    if not user:
        return await message.reply("⚠️ User not found in database.")
    username = user.get("username")
    username_display = f"@{username}" if username else "N/A"
    last_date = user.get("last_date", "N/A")
    expiry_time = user.get("expiry_time")
    if isinstance(last_date, datetime):
        last_date = last_date.strftime("%Y-%m-%d")
    is_premium = await db.has_premium_access(user_id)
    daily_limit = PREMIUM_DAILY_LIMIT if is_premium else DAILY_LIMIT
    used = await db.get_video_count(user_id)
    remaining = max(daily_limit - used, 0)
    subscription_type = "Paid" if is_premium else "Free"
    if isinstance(expiry_time, datetime):
        # Timezone conversion for display
        try:
            if expiry_time.tzinfo is None:
                expiry_time = pytz.utc.localize(expiry_time)
            expiry_dt = expiry_time.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_date = expiry_dt.strftime('%d-%m-%Y')
            expiry_clock = expiry_dt.strftime('%I:%M:%S %p')
        except:
            expiry_date = "Error"
            expiry_clock = "Error"
    else:
        expiry_date = "N/A"
        expiry_clock = "N/A"
    text = f"""**👤 User Info**

🆔 User ID: `{user_id}`
📛 Username: {username_display}
📆 Last Active: `{last_date}`

**📦 Plan Details**
💠 Subscription: `{subscription_type}`
📁 Daily Limit: `{daily_limit} Files`
📤 Files Used: `{used}/{daily_limit}`
🟢 Remaining: `{remaining} Files`
"""

    if is_premium:
        text += f"""**💎 Premium Info**
📅 Expiry Date: `{expiry_date}`
⏰ Expiry Time: `{expiry_clock}`
"""

    await message.reply(text)
                    
