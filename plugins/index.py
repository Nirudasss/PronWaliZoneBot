import asyncio
import time
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, ChannelInvalid, ChatAdminRequired
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from info import ADMINS, VIDEO_CHANNEL
from database.users_db import db  
from utils import temp, get_progress_bar, get_readable_time

# Global Lock and Cache
lock = asyncio.Lock()
INDEX_CACHE = {}

# =================================================
# 📥 CALLBACK QUERY HANDLER (Fixed)
# =================================================
@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    # Split data: index#action
    data_parts = query.data.split("#")
    if len(data_parts) < 2:
        await query.answer("❌ Invalid Data", show_alert=True)
        return

    action = data_parts[1] # yes, start_main, start_brazzers, cancel
    user_id = query.from_user.id

    # 1. Cancel Action
    if action == 'cancel':
        temp.CANCEL = True
        # Clear cache if exists
        if user_id in INDEX_CACHE:
            del INDEX_CACHE[user_id]
        
        try:
            await query.message.edit("🛑 Indexing Cancelled.")
        except:
            await query.answer("🛑 Indexing Cancelled.")
        return

    # 2. Check if data exists in cache
    if user_id not in INDEX_CACHE:
        await query.answer("⚠️ Session Expired. Please use /index again.", show_alert=True)
        
        # --- FIX: Prevent Crash on Delete ---
        try:
            if query.message:
                await query.message.delete()
        except Exception:
            pass # Ignore if message or chat is invalid
        return

    # Fetch Data from Cache
    data = INDEX_CACHE[user_id]
    chat = data['chat']
    lst_msg_id = data['lst_msg_id']
    skip = data['skip']

    # Step 1: Selection Menu
    if action == 'yes':
        buttons = [
            [
                InlineKeyboardButton('🎬 Video Index', callback_data=f'index#start_main'),
                InlineKeyboardButton('🔞 Brazzers Index', callback_data=f'index#start_brazzers')
            ],
            [
                InlineKeyboardButton('❌ Cancel', callback_data='index#cancel')
            ]
        ]
        
        await query.message.edit(
            text="<b>📂 Select Database to Save Files:</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # Step 2: Start Indexing
    elif action.startswith('start_'):
        target_db = action.replace('start_', '') # 'main' or 'brazzers'
        db_name = "Brazzers" if target_db == "brazzers" else "Main Video"
        
        await query.message.edit(
            f"<b>🚀 {db_name} Indexing started...</b>\n"
            f"🔹 Chat: {chat}\n"
            f"🔹 Starting from: {skip}"
        )
        
        # Start Indexing Process
        await index_files_to_db(lst_msg_id, chat, query.message, bot, skip, target_db)
        
        # Cleanup Cache after finish
        if user_id in INDEX_CACHE:
            del INDEX_CACHE[user_id]

# =================================================
# 📥 COMMAND HANDLER (/index)
# =================================================
@Client.on_message(filters.command('index') & filters.private & filters.incoming & filters.user(ADMINS))
async def send_for_index(bot, message):
    if lock.locked():
        return await message.reply('⚠️ Wait until previous process completes.')
        
    i = await message.reply("Forward last message from channel OR send last message link.")
    
    try:
        msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    except Exception as e:
        return await message.reply(f"Listener Error: {e}")
    
    await i.delete()
    
    last_msg_id = 0
    chat_id = None
    
    # Parse Link or Forward
    if msg.text and msg.text.startswith("https://t.me"):
        try:
            parts = msg.text.split("/")
            last_msg_id = int(parts[-1])
            chat_id_str = parts[-2]
            if chat_id_str.isdigit():
                chat_id = int(f"-100{chat_id_str}")
            else:
                chat_id = chat_id_str
        except:
            await message.reply('❌ Invalid message link!')
            return
    elif msg.forward_from_chat and msg.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = msg.forward_from_message_id
        chat_id = msg.forward_from_chat.id
    else:
        await message.reply('❌ This is not a forwarded message or valid link.')
        return

    # Verify Channel
    try:
        chat = await bot.get_chat(chat_id)
        if chat.type != enums.ChatType.CHANNEL:
            return await message.reply("I can index only channels.")
    except Exception as e:
        return await message.reply(f'Error getting chat: {e}')

    # Ask for Skip
    s = await message.reply("Send skip message number (e.g., 0).")
    try:
        msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
        skip = int(msg.text)
    except:
        await s.delete()
        return await message.reply("❌ Invalid Number.")
    await s.delete()

    # Store Data in Cache
    INDEX_CACHE[message.from_user.id] = {
        'chat': chat.id,
        'lst_msg_id': last_msg_id,
        'skip': skip
    }

    buttons = [[
        InlineKeyboardButton('YES', callback_data='index#yes')
    ],[
        InlineKeyboardButton('CLOSE', callback_data='close_data'),
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await message.reply(
        f'Do you want to index <b>{chat.title}</b>?\n\n'
        f'🆔 ID: <code>{chat.id}</code>\n'
        f'📨 Total Messages: <code>{last_msg_id}</code>\n'
        f'⏭ Skip: <code>{skip}</code>',
        reply_markup=reply_markup
    )

# =================================================
# ⚙️ MAIN INDEXING LOGIC
# =================================================
async def index_files_to_db(lst_msg_id, chat, msg, bot, skip, target_db):
    start_time = time.time()
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    current = skip + 1 
    BATCH_SIZE = 20

    async with lock:
        try:
            temp.CANCEL = False
            
            while current <= lst_msg_id:
                
                if temp.CANCEL:
                    time_taken = get_readable_time(time.time()-start_time)
                    await msg.edit(f"🛑 Indexing Cancelled!\n⏱ Time: {time_taken}\n✅ Saved: {total_files}")
                    return

                end_id = min(current + BATCH_SIZE, lst_msg_id + 1)
                ids = list(range(current, end_id))
                
                if not ids:
                    break

                try:
                    messages = await bot.get_messages(chat, ids)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    messages = await bot.get_messages(chat, ids)
                except Exception as e:
                    print(f"Batch Error: {e}")
                    errors += len(ids)
                    current += BATCH_SIZE
                    continue

                for message in messages:
                    if temp.CANCEL: break
                    
                    try:
                        # 1. Validation Checks
                        if not message or message.empty:
                            deleted += 1
                            continue
                        
                        if not message.media:
                            no_media += 1
                            continue
                        
                        if message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT]:
                            unsupported += 1
                            continue
                        
                        media = getattr(message, message.media.value, None)
                        if not media:
                            unsupported += 1
                            continue
                        
                        file_id = media.file_id
                        file_unique_id = media.file_unique_id
                        
                        # 2. Database Insertion
                        if target_db == "brazzers":
                            # Ensure your DB function supports this
                            is_new = await db.add_brazzers_video(file_unique_id, file_id)
                        else:
                            is_new = await db.add_video(file_unique_id, file_id)
                        
                        # Handle case where DB function returns None
                        if is_new is None: 
                            is_new = True 

                        if is_new:
                            total_files += 1
                        else:
                            duplicate += 1

                    except Exception as e:
                        print(f"Message Error: {e}")
                        errors += 1

                # 3. Update Loop & UI
                current += BATCH_SIZE
                
                # Update UI every batch
                percentage = (min(current, lst_msg_id) / lst_msg_id) * 100
                prog_bar = get_progress_bar(percentage)
                elapsed_time = get_readable_time(time.time() - start_time)
                
                db_label = "🔞 Brazzers" if target_db == "brazzers" else "🎬 Video"
                btn = [[InlineKeyboardButton('CANCEL', callback_data=f'index#cancel')]]
                
                try:
                    await msg.edit(
                        f"📊 <b>{db_label} Indexing Progress</b>\n"
                        f"{prog_bar} {percentage:.1f}%\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"📥 Scanned: <code>{min(current, lst_msg_id)}/{lst_msg_id}</code>\n"
                        f"✅ Saved: <code>{total_files}</code>\n"
                        f"♻️ Duplicates: <code>{duplicate}</code>\n"
                        f"🗑 Deleted/Skip: <code>{deleted + no_media + unsupported}</code>\n"
                        f"⚠️ Errors: <code>{errors}</code>\n"
                        f"⏱ Elapsed: <code>{elapsed_time}</code>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                except FloodWait as e:
                    await asyncio.sleep(e.value) 
                except Exception:
                    pass

            # Final Message
            time_taken = get_readable_time(time.time()-start_time)
            db_label = "🔞 Brazzers" if target_db == "brazzers" else "🎬 Video"
            
            await msg.edit(
                f"✅ <b>{db_label} Indexing Completed!</b>\n"
                f"⏱ Time: {time_taken}\n"
                f"📥 Total Scanned: <code>{lst_msg_id}</code>\n"
                f"✅ Saved: <code>{total_files}</code>\n"
                f"♻️ Duplicates: <code>{duplicate}</code>\n"
                f"🗑 Deleted: <code>{deleted}</code>\n"
                f"🚫 Non-Media: <code>{no_media + unsupported}</code>\n"
                f"⚠️ Errors: <code>{errors}</code>"
            )

        except Exception as e:
            await msg.edit(f"❌ Critical Error: {e}")
            
