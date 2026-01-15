from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from Script import script
from database.users_db import db
from info import DAILY_LIMIT, PREMIUM_DAILY_LIMIT, ADMINS, LOG_CHANNEL, PREMIUM_LOGS, OWNER_USERNAME, UPI_ID, QR_CODE_IMAGE
from datetime import timedelta
import pytz, datetime, time, asyncio
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
from utils import temp, get_seconds

# -------------------------------------------------------------------------
# 📋 ADMIN: LIST PREMIUM USERS
# -------------------------------------------------------------------------
@Client.on_message(filters.command("premium_user") & filters.user(ADMINS))
async def premium_user(client, message):
    aa = await message.reply_text("Fetching ...")  
    users = await db.get_all_users()
    users_list = []
    async for user in users:
        users_list.append(user)    
    user_data = {user['id']: await db.get_user(user['id']) for user in users_list}    
    new_users = []
    for user in users_list:
        user_id = user['id']
        data = user_data.get(user_id)
        expiry = data.get("expiry_time") if data else None        
        if expiry:
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_str_in_ist = expiry_ist.strftime("%d-%m-%Y %I:%M:%S %p")          
            current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            time_left = expiry_ist - current_time
            days, remainder = divmod(time_left.total_seconds(), 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)            
            time_left_str = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"            
            user_info = await client.get_users(user_id)
            user_str = (
                f"{len(new_users) + 1}. User ID: {user_id}\n"
                f"Name: {user_info.mention}\n"
                f"Expiry Date: {expiry_str_in_ist}\n"
                f"Expiry Time: {time_left_str}\n\n"
            )
            new_users.append(user_str)
    new = "Paid Users - \n\n" + "\n".join(new_users)   
    try:
        await aa.edit_text(new)
    except MessageTooLong:
        with open('usersplan.txt', 'w+') as outfile:
            outfile.write(new)
        await message.reply_document('usersplan.txt', caption="Paid Users:")

# -------------------------------------------------------------------------
# 🛍️ BUY COMMAND (Shows Plan & QR Code)
# -------------------------------------------------------------------------
@Client.on_message(filters.command("buy") | filters.regex(r"(?i)Subscription"))
async def buy_handler(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    is_premium = await db.has_premium_access(user_id)
    user_username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    log_text = (
        f"#Buy_Command_Used\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"👤 Name: {username}\n"
        f"💬 Username: {user_username}\n"
    )
    
    try:
        await client.send_message(PREMIUM_LOGS, log_text)
    except Exception as e:
        print(f"Failed to send log to PREMIUM_LOGS: {e}")
    if is_premium:
        await message.reply_text("✅ 𝖸𝗈𝗎 �𝖠𝗅𝗋𝖾𝖺𝖽𝗒 𝖯𝗎𝗋𝖼𝗁𝖺𝗌𝖾𝖽 �𝖮𝗎𝗋 𝖲𝗎𝖻𝗌𝖼𝗋𝗂𝗉𝗍𝗂𝗈𝗇! 𝖤𝗇𝗃𝗈𝗒 𝖸𝗈𝗎𝗋 𝖡𝖾𝗇𝖾𝖿𝗂𝗍.", quote=True)
        return
    text = script.SEENBUY_TXT.format(DAILY_LIMIT, PREMIUM_DAILY_LIMIT, UPI_ID)
    btn = [
        [InlineKeyboardButton('✖️ ᴄʟᴏsᴇ ✖️', callback_data='close_data')]
    ]
    if QR_CODE_IMAGE:
        await message.reply_photo(
            photo=QR_CODE_IMAGE,
            caption=text,
            reply_markup=InlineKeyboardMarkup(btn)
        )
    else:
        await message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(btn)
        )

# -------------------------------------------------------------------------
# 📸 SCREENSHOT HANDLER (Direct Auto-Forward to Admin)
# -------------------------------------------------------------------------
@Client.on_message(filters.photo & filters.private)
async def payment_screenshot_handler(client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.mention
    user_note = message.caption if message.caption else "No caption provided"
    msg = await message.reply_text("🔄 𝘚𝘦𝘯𝘥𝘪𝘯𝘨 𝘱𝘢𝘺𝘮𝘦𝘯𝘵 𝘴𝘤𝘳𝘦𝘦𝘯𝘴𝘩𝘰𝘵 𝘵𝘰 𝘈𝘥𝘮𝘪𝘯𝘴... 𝘗𝘭𝘦𝘢𝘴𝘦 𝘸𝘢𝘪𝘵.")
    admin_btns = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve (1 Day)", callback_data=f"add_prem_{user_id}_1"),
            InlineKeyboardButton("✅ Approve (1 Week)", callback_data=f"add_prem_{user_id}_7")
        ],
        [
            InlineKeyboardButton("✅ Approve (1 Month)", callback_data=f"add_prem_{user_id}_30")
        ],
        [
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_pay_{user_id}")
        ]
    ])
    
    try:
        await client.send_photo(
            chat_id=PREMIUM_LOGS,
            photo=message.photo.file_id,
            caption=f"🧾 **New Payment Screenshot**\n\n👤 <b>User:</b> {user_name}\n🆔 <b>ID:</b> <code>{user_id}</code>\n📝 <b>Note:</b> {user_note}",
            reply_markup=admin_btns
        )
        await msg.edit_text("✅ 𝘚𝘤𝘳𝘦𝘦𝘯𝘴𝘩𝘰𝘵 𝘴𝘦𝘯𝘵!\n𝘈𝘥𝘮𝘪𝘯 𝘸𝘪𝘭𝘭 𝘷𝘦𝘳𝘪𝘧𝘺 𝘢𝘯𝘥 𝘢𝘤𝘵𝘪𝘷𝘢𝘵𝘦 𝘺𝘰𝘶𝘳 𝘱𝘭𝘢𝘯 𝘴𝘩𝘰𝘳𝘵𝘭𝘺.")
    except Exception as e:
        await msg.edit_text(f"❌ Error sending to admin: {e}")

# -------------------------------------------------------------------------
# ✅ APPROVE PAYMENT CALLBACK
# -------------------------------------------------------------------------
@Client.on_callback_query(filters.regex(r"^add_prem_"))
async def approve_payment(client, callback_query: CallbackQuery):
    _, _, user_id, days = callback_query.data.split("_")
    user_id = int(user_id)
    days = int(days)
    new_expiry = await db.add_premium_access(user_id, days)
    expiry_ist = new_expiry.astimezone(pytz.timezone("Asia/Kolkata"))
    expiry_str = expiry_ist.strftime("%d-%m-%Y %I:%M %p")
    try:
        await client.send_message(
            user_id,
            f"🎉 <b>𝘗𝘢𝘺𝘮𝘦𝘯𝘵 𝘈𝘱𝘱𝘳𝘰𝘷𝘦𝘥!</b>\n\n💎 <b>𝘗𝘳𝘦𝘮𝘪𝘶𝘮 𝘈𝘤𝘵𝘪𝘷𝘢𝘵𝘦𝘥</b> 𝘧𝘰𝘳 {days} 𝘋𝘢𝘺𝘴 .\n🗓 <b>𝘌𝘹𝘱𝘪𝘳𝘺:</b> {expiry_str}\n\n<i>𝘌𝘯𝘫𝘰𝘺 𝘜𝘯𝘭𝘪𝘮𝘪𝘵𝘦𝘥 𝘈𝘤𝘤𝘦𝘴𝘴!</i>"
        )
    except:
        pass 
    await callback_query.message.edit_caption(
        caption=f"✅ <b>Approved by {callback_query.from_user.mention}</b>\n\n🆔 User: <code>{user_id}</code>\n⏳ Added: {days} Days"
    )

# -------------------------------------------------------------------------
# ❌ REJECT PAYMENT CALLBACK
# -------------------------------------------------------------------------
@Client.on_callback_query(filters.regex(r"^reject_pay_"))
async def reject_payment(client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[2])
    try:
        await client.send_message(
            user_id,
            f"❌ <b>𝘗𝘢𝘺𝘮𝘦𝘯𝘵 𝘙𝘦𝘫𝘦𝘤𝘵𝘦𝘥.</b>\n\n<i>𝘗𝘰𝘴𝘴𝘪𝘣𝘭𝘦 𝘳𝘦𝘢𝘴𝘰𝘯𝘴:</i>\n- 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘚𝘤𝘳𝘦𝘦𝘯𝘴𝘩𝘰𝘵\n- 𝘗𝘢𝘺𝘮𝘦𝘯𝘵 𝘯𝘰𝘵 𝘳𝘦𝘤𝘦𝘪𝘷𝘦𝘥\n- 𝘞𝘳𝘰𝘯𝘨 𝘈𝘮𝘰𝘶𝘯𝘵 \n\n<i>𝘊𝘰𝘯𝘵𝘢𝘤𝘵 𝘈𝘥𝘮𝘪𝘯 𝘧𝘰𝘳 𝘴𝘶𝘱𝘱𝘰𝘳𝘵. @{OWNER_USERNAME}</i>"
        )
    except:
        pass
    await callback_query.message.edit_caption(
        caption=f"❌ <b>Rejected by {callback_query.from_user.mention}</b>\n\n🆔 User: <code>{user_id}</code>"
    )

# -------------------------------------------------------------------------
# 👤 MY PLAN COMMAND
# -------------------------------------------------------------------------
@Client.on_message((filters.command("myplan") | filters.regex(r"(?i)^my\s?plan$")) & filters.private)
async def myplan_handler(_, m: Message):
    user_id = m.from_user.id
    username = m.from_user.first_name
    used = await db.get_video_count(user_id)
    is_premium = await db.has_premium_access(user_id)
    premium_details = await db.get_user(user_id) if is_premium else None
    daily_limit = PREMIUM_DAILY_LIMIT if is_premium else DAILY_LIMIT
    remaining = max(daily_limit - used, 0)
    subscription_type = "𝖯𝖺𝗂𝖽" if is_premium else "𝖥𝗋𝖾𝖾"
    
    text = f"""📊 <blockquote>**𝖯𝗅𝖺𝗇 𝖣𝖾𝗍𝖺𝗂𝗅𝗌**</blockquote>

👤 <b>𝖴𝗌𝖾𝗋 𝖺𝗆𝖾:</b> {username}
🆔 <b>𝖴𝗌𝖾𝗋 𝖨𝖣 :</b> <code>{user_id}</code>
💠 <b>𝖲𝗎𝖻𝗌𝖼𝗋𝗂𝗉𝗍𝗂𝗈𝗇:</b> {subscription_type}
📂 <b>𝖣𝖺𝗂𝗅𝗒 𝖫𝗂𝗆𝗂𝗍:</b> {daily_limit} 𝖥𝗂𝗅𝖾𝗌
📉 <b>𝖴𝗌𝖾𝖽:</b> {used} | <b>𝖫𝖾𝖿𝗍:</b> {remaining}"""

    if is_premium and premium_details and premium_details.get('expiry_time'):
        expiry = premium_details['expiry_time']
        if expiry.tzinfo is None:
            expiry = pytz.utc.localize(expiry)
        expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
        text += f"""

⏳ <blockquote>**𝖲𝗎𝖻𝗌𝖼𝗋𝗂𝗉𝗍𝗂𝗈𝗇 𝖣𝖾𝗍𝖺𝗂𝗅𝗌**</blockquote>
<i> 📅 𝖤𝗑𝗉𝗂𝗋𝗒 𝖣𝖺𝗍𝖾 - {expiry_ist.strftime('%d-%m-%Y')}
⏰ 𝖤𝗑𝗉𝗂𝗋𝗒 𝖳𝗂𝗆𝖾 - {expiry_ist.strftime('%I:%M %p')}</i>"""

    await m.reply(text)
        
# -------------------------------------------------------------------------
# 🛠 ADMIN COMMAND: ADD PREMIUM (Manual)
# -------------------------------------------------------------------------
@Client.on_message(filters.command("add_premium") & filters.user(ADMINS))
async def give_premium_cmd_handler(client, message):
    if len(message.command) == 4:
        time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ ᴊᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p") 
        user_id = int(message.command[1])  
        try:
            user = await client.get_users(user_id)
        except:
            await message.reply_text("Invalid user ID")
            return
        
        # Renamed variable from 'time' to 'duration' to avoid conflict with import time
        duration = message.command[2] + " " + message.command[3]
        seconds = await get_seconds(duration)
        
        if seconds > 0:
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            user_data = {"id": user_id, "expiry_time": expiry_time}  
            await db.update_user(user_data) 
            data = await db.get_user(user_id)
            expiry = data.get("expiry_time")   
            
            # Ensure expiry is timezone aware if necessary, or assume naive from DB
            if expiry.tzinfo is None:
                 expiry = pytz.utc.localize(expiry) # Assuming stored as UTC or Naive

            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")
            expiry_str_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y 𝘈𝘵 : %I:%M:%S %p")         
            
            await message.reply_text(f"ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\n👤 ᴜꜱᴇʀ : {user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{duration}</code>\n\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True)
            try:
                await client.send_message(
                    chat_id=user_id,
                    text=f"🎉 𝘊𝘰𝘯𝘨𝘳𝘢𝘵𝘶𝘭𝘢𝘵𝘪𝘰𝘯𝘴! 𝘠𝘰𝘶'𝘷𝘦 𝘨𝘰𝘵 𝘗𝘳𝘦𝘮𝘪𝘶𝘮 𝘈𝘤𝘤𝘦𝘴𝘴!\n\n⏳ 𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯 : {duration}\n📅 𝘌𝘹𝘱𝘪𝘳𝘺 : {expiry_str_ist}\n\n✨ 𝘌𝘯𝘫𝘰𝘺 𝘺𝘰𝘶𝘳 𝘱𝘳𝘦𝘮𝘪𝘶𝘮 𝘣𝘦𝘯𝘦𝘧𝘪𝘵𝘴!", disable_web_page_preview=True             
                )    
            except:
                pass
                
            await client.send_message(PREMIUM_LOGS, text=f"#Added_Premium\n\n👤 ᴜꜱᴇʀ : {user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{duration}</code>\n\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True)
                    
        else:
            await message.reply_text("Invalid time format. Please use '1 day', '1 hour', '1 min', '1 month', or '1 year'")
    else:
        await message.reply_text("Usage : /add_premium user_id time (e.g., '1 day', '1 hour', '1 min', '1 month', or '1 year')")

# -------------------------------------------------------------------------
# 🛠 ADMIN COMMAND: REMOVE PREMIUM
# -------------------------------------------------------------------------
@Client.on_message(filters.command("remove_premium") & filters.user(ADMINS))
async def remove_premium(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])
        try:
            user = await client.get_users(user_id)
        except:
            await message.reply_text("Invalid user ID")
            return
            
        if await db.remove_premium_access(user_id):
            await message.reply_text("ᴜꜱᴇʀ ʀᴇᴍᴏᴠᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ !")
            try:
                await client.send_message(
                    chat_id=user_id,
                    text=f"<b>ʜᴇʏ {user.mention},\n\n𝖸𝗈𝗎𝗋 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 𝖠𝖼𝖼𝖾𝗌𝗌 𝗁𝖺𝗌 𝖻𝖾𝖾𝗇 𝗋𝖾𝗆𝗈𝗏𝖾𝖽.</b>"
                )
            except:
                pass
        else:
            await message.reply_text("ᴜɴᴀʙʟᴇ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴜꜱᴇʀ !\nᴀʀᴇ ʏᴏᴜ ꜱᴜʀᴇ, ɪᴛ ᴡᴀꜱ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ɪᴅ ?")
    else:
        await message.reply_text("ᴜꜱᴀɢᴇ : /remove_premium user_id")
        
