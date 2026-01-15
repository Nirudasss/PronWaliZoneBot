from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_db import db
from utils import temp
from Script import script
import datetime
from info import PREMIUM_LOGS

@Client.on_message(filters.command(["invite", "refer"]))
async def invite_command_handler(client, message):
    user_id = message.from_user.id
    is_premium = await db.has_premium_access(user_id)
    ref_link = f"https://t.me/{temp.U_NAME}?start=reff_{user_id}"
    share_link = f"https://telegram.me/share/url?url={ref_link}&text=Join%20Now%20For%20Movies!"
    if is_premium:
        await message.reply_text("✅ 𝖸𝗈𝗎 �𝖠𝗅𝗋𝖾𝖺𝖽𝗒 𝖯𝗎𝗋𝖼𝗁𝖺𝗌𝖾𝖽 �𝖮𝗎𝗋 𝖲𝗎𝖻𝗌𝖼𝗋𝗂𝗉𝗍𝗂𝗈𝗇! 𝖤𝗇𝗃𝗈𝗒 𝖸𝗈𝗎𝗋 𝖡𝖾𝗇𝖾𝖿𝗂𝗍.", quote=True)
        return
    buttons = [[
        InlineKeyboardButton("• ɪɴᴠɪᴛᴇ ʟɪɴᴋ •", url=share_link)
    ],[
        InlineKeyboardButton('✖️ ᴄʟᴏsᴇ ✖️', callback_data='close_data')
    ]]
    await message.reply_text(
        text=script.REFER_TEXT.format(message.from_user.mention, ref_link),
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True,
        parse_mode=enums.ParseMode.HTML
    )

async def refer_on_start(client, message):
    user_id = message.from_user.id
    mention = message.from_user.mention
    argument = message.command[1]
    try:
        inviter_id = int(argument.split("_")[1])
    except:
        return await message.reply_text("❌ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘙𝘦𝘧𝘦𝘳 𝘓𝘪𝘯𝘬!")
    if inviter_id == user_id:
        return await message.reply_text("<b>𝘠𝘰𝘶 𝘤𝘢𝘯𝘯𝘰𝘵 𝘳𝘦𝘧𝘦𝘳 𝘺𝘰𝘶𝘳𝘴𝘦𝘭𝘧! 🤣</b>")

    if await db.is_user_exist(user_id):
        return await message.reply_text("<b>𝘠𝘰𝘶 𝘢𝘳𝘦 𝘢𝘭𝘳𝘦𝘢𝘥𝘺 𝘢 𝘶𝘴𝘦𝘳!</b>")

    try:
        inviter = await client.get_users(inviter_id)
    except:
        return await message.reply_text("❌ 𝘐𝘯𝘷𝘢𝘭𝘪𝘥 𝘐𝘯𝘷𝘪𝘵𝘦𝘳 𝘐𝘋!")

    await db.add_user(user_id, message.from_user.first_name)

    current_points = await db.get_refer_points(inviter_id) or 0
    new_total = current_points + 10

    await message.reply_text(
        f"✅ 𝘠𝘰𝘶 𝘩𝘢𝘷𝘦 𝘣𝘦𝘦𝘯 𝘴𝘶𝘤𝘤𝘦𝘴𝘴𝘧𝘶𝘭𝘭𝘺 𝘪𝘯𝘷𝘪𝘵𝘦𝘥 𝘣𝘺 {inviter.mention}!"
    )

    # 🎁 Reward System
    if new_total >= 10:
        expiry_time = datetime.datetime.now() + datetime.timedelta(hours=1)

        await db.update_user({
            "id": inviter_id,
            "expiry_time": expiry_time
        })

        # Reset points
        await db.set_refer_points(inviter_id, 0)

        try:
            await client.send_message(
                PREMIUM_LOGS,
                script.PREMIUM_REFERRAL_LOG.format(
                    inviter=inviter.mention,
                    inviter_id=inviter_id,
                    user=mention,
                    user_id=user_id
                )
            )
        except:
            pass

        await client.send_message(
            inviter_id,
            f"🎉 𝖢𝗈𝗇𝗀𝗋𝖺𝗍𝗎𝗅𝖺𝗍𝗂𝗈𝗇𝗌 {inviter.mention}!\n\n"
            "𝖸𝗈𝗎 𝖼𝗈𝗅𝗅𝖾𝖼𝗍𝖾𝖽 10 𝖯𝗈𝗂𝗇𝗍𝗌 𝖺𝗇𝖽 𝗐𝗈𝗇 1 Hour 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 𝖲𝗎𝖻𝗌𝖼𝗋𝗂𝗉𝗍𝗂𝗈𝗇!"
        )

    else:
        await db.set_refer_points(inviter_id, new_total)
        await client.send_message(
            inviter_id,
            text=f"✈️ 𝖭𝖾𝗐 𝖱𝖾𝖿𝖾𝗋𝗋𝖺𝗅!\n\n{mention} 𝗃𝗈𝗂𝗇𝖾𝖽 𝗏𝗂𝖺 𝗒𝗈𝗎𝗋 𝗅𝗂𝗇𝗄.\n➕ +10 𝖯𝗈𝗂𝗇𝗍𝗌\n💰 𝖳𝗈𝗍𝖺𝗅: {new_total}"
            )
