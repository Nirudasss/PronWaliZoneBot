import asyncio
import time
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from info import ADMINS
from database.users_db import db  
from utils import temp, get_progress_bar, get_readable_time

lock = asyncio.Lock()

# ---------------------------
# GLOBAL STORES
# ---------------------------
INDEX_CACHE = {}
if not hasattr(temp, "CANCEL_USERS"):
    temp.CANCEL_USERS = set()

# =================================================
# 📥 CALLBACK QUERY HANDLER (FIXED)
# =================================================
@Client.on_callback_query(filters.regex(r'^index#'))
async def index_files(bot, query):
    action = query.data.split("#")[1]
    user_id = query.from_user.id

    # ---------------- CANCEL ----------------
    if action == 'cancel':
        temp.CANCEL_USERS.add(user_id)
        INDEX_CACHE.pop(user_id, None)
        await query.message.edit("🛑 Indexing Cancelled.")
        return

    # ---------------- SESSION CHECK ----------------
    if user_id not in INDEX_CACHE:
        await query.answer("⚠️ Session Expired. Please use /index again.", show_alert=True)
        await query.message.delete()
        return

    data = INDEX_CACHE[user_id]
    chat = data['chat']
    lst_msg_id = data['lst_msg_id']
    skip = data['skip']

    # ---------------- FIRST CONFIRM ----------------
    if action == 'yes':
        buttons = [
            [
                InlineKeyboardButton('🎬 Video Index', callback_data='index#start_main'),
                InlineKeyboardButton('🔞 Brazzers Index', callback_data='index#start_brazzers')
            ],
            [InlineKeyboardButton('❌ No Index', callback_data='index#cancel')]
        ]
        await query.message.edit(
            text="<b>📂 Select Database to Save Files:</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # ---------------- START INDEX ----------------
    if action.startswith('start_'):
        target_db = action.replace('start_', '')
        db_name = "Brazzers" if target_db == "brazzers" else "Main Video"

        await query.message.edit(f"<b>🚀 {db_name} Indexing started from ID: {skip}...</b>")
        await index_files_to_db(lst_msg_id, chat, query.message, bot, skip, target_db, user_id)

        INDEX_CACHE.pop(user_id, None)

# =================================================
# ❌ CLOSE BUTTON HANDLER
# =================================================
@Client.on_callback_query(filters.regex("^close_data$"))
async def close_data_cb(bot, query):
    await query.message.delete()

# =================================================
# 📥 COMMAND HANDLER (/index)
# =================================================
@Client.on_message(filters.command('index') & filters.private & filters.incoming & filters.user(ADMINS))
async def send_for_index(bot, message: Message):
    if lock.locked():
        return await message.reply('⚠️ Wait until previous process completes.')

    ask = await message.reply("Forward last message from channel OR send last message link.")
    try:
        msg = await bot.listen(message.chat.id, message.from_user.id, timeout=60)
    except asyncio.TimeoutError:
        return await message.reply("⏳ Time out! Try again.")
    finally:
        await ask.delete()

    last_msg_id = 0
    chat_id = None

    if msg.text and msg.text.startswith("https://t.me"):
        try:
            parts = msg.text.split("/")
            last_msg_id = int(parts[-1])
            chat_id_str = parts[-2]
            chat_id = int(f"-100{chat_id_str}") if chat_id_str.isdigit() else chat_id_str
        except:
            return await message.reply('❌ Invalid message link!')

    elif msg.forward_from_chat and msg.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = msg.forward_from_message_id
        chat_id = msg.forward_from_chat.id
    else:
        return await message.reply('❌ This is not a forwarded message or valid link.')

    try:
        chat = await bot.get_chat(chat_id)
        if chat.type != enums.ChatType.CHANNEL:
            return await message.reply("I can index only channels.")
    except Exception as e:
        return await message.reply(f'Error: {e}')

    ask_skip = await message.reply("Send skip message number (e.g., 0).")
    try:
        msg = await bot.listen(message.chat.id, message.from_user.id, timeout=60)
        skip = int(msg.text)
    except:
        await ask_skip.delete()
        return await message.reply("❌ Invalid Number.")
    await ask_skip.delete()

    INDEX_CACHE[message.from_user.id] = {
        'chat': chat.id,
        'lst_msg_id': last_msg_id,
        'skip': skip
    }

    buttons = [
        [InlineKeyboardButton('YES', callback_data='index#yes')],
        [InlineKeyboardButton('CLOSE', callback_data='close_data')]
    ]

    await message.reply(
        f'Do you want to index <b>{chat.title}</b>?\n\n'
        f'🆔 ID: <code>{chat.id}</code>\n'
        f'📨 Total Messages: <code>{last_msg_id}</code>\n'
        f'⏭ Skip: <code>{skip}</code>',
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# =================================================
# ⚙️ MAIN INDEXING LOGIC (FIXED)
# =================================================
async def index_files_to_db(lst_msg_id, chat, msg, bot, skip, target_db, user_id):
    start_time = time.time()
    total_files = duplicate = errors = deleted = no_media = unsupported = 0
    current = skip + 1
    BATCH_SIZE = 20

    async with lock:
        try:
            temp.CANCEL_USERS.discard(user_id)

            while current <= lst_msg_id:

                if user_id in temp.CANCEL_USERS:
                    time_taken = get_readable_time(time.time()-start_time)
                    await msg.edit(f"🛑 Indexing Cancelled!\n⏱ Time: {time_taken}\n✅ Saved: {total_files}")
                    return

                end_id = min(current + BATCH_SIZE - 1, lst_msg_id)
                ids = list(range(current, end_id + 1))

                try:
                    messages = await bot.get_messages(chat, ids)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    messages = await bot.get_messages(chat, ids)
                except:
                    errors += len(ids)
                    current += BATCH_SIZE
                    continue

                for m in messages:
                    if user_id in temp.CANCEL_USERS:
                        break
                    try:
                        if not m or m.empty:
                            deleted += 1
                            continue

                        if not m.media:
                            no_media += 1
                            continue

                        if m.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT]:
                            unsupported += 1
                            continue

                        media = getattr(m, m.media.value, None)
                        if not media:
                            unsupported += 1
                            continue

                        fid = media.file_id
                        fuid = media.file_unique_id

                        if target_db == "brazzers":
                            is_new = await db.add_brazzers_video(fuid, fid) or True
                        else:
                            is_new = await db.add_video(fuid, fid)

                        if is_new:
                            total_files += 1
                        else:
                            duplicate += 1

                    except Exception:
                        errors += 1

                current += BATCH_SIZE

                scanned = min(current - 1, lst_msg_id)
                percentage = (scanned / lst_msg_id) * 100
                prog_bar = get_progress_bar(percentage)
                elapsed_time = get_readable_time(time.time() - start_time)

                db_label = "🔞 Brazzers" if target_db == "brazzers" else "🎬 Video"
                btn = [[InlineKeyboardButton('CANCEL', callback_data='index#cancel')]]

                try:
                    await msg.edit(
                        f"📊 <b>{db_label} Indexing Progress</b>\n"
                        f"{prog_bar} {percentage:.1f}%\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"📥 Scanned: <code>{scanned}/{lst_msg_id}</code>\n"
                        f"✅ Saved: <code>{total_files}</code>\n"
                        f"♻️ Duplicates: <code>{duplicate}</code>\n"
                        f"🗑 Deleted/Skip: <code>{deleted + no_media + unsupported}</code>\n"
                        f"⚠️ Errors: <code>{errors}</code>\n"
                        f"⏱ Elapsed: <code>{elapsed_time}</code>",
                        reply_markup=InlineKeyboardMarkup(btn)
                    )
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except:
                    pass

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
