from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from info import VIDEO_CHANNEL, BRAZZER_CHANNEL, NO_IMG, POST_CHANNEL, POST_SHORTLINK, SEND_POST
from database.users_db import db
from utils import temp, get_shortlink, generate_weird_name, generate_thumbnail

# -----------------------
# BRAZZERS INDEX
# -----------------------
@Client.on_message(filters.video & filters.chat(BRAZZER_CHANNEL))
async def index_brazzers_videos(_, m: Message):
    file_id = m.video.file_id
    file_unique_id = m.video.file_unique_id
    await db.add_brazzers_video(file_unique_id, file_id)

# -----------------------
# NORMAL VIDEO INDEX
# -----------------------
@Client.on_message(filters.video & filters.chat(VIDEO_CHANNEL))
async def index_normal_videos(client, m: Message):
    try:
        file_id = m.video.file_id
        file_unique_id = m.video.file_unique_id

        # 🔥 Weird random name
        file_name = generate_weird_name() + ".mp4"

        # DB
        status = await db.add_video(file_unique_id, file_id)

        if status:
            print(f"✅ New Video Added: {file_name} (Msg ID: {m.id})")
        else:
            print(f"♻️ Duplicate Found: {file_name}")

        # SEND_POST check
        if not SEND_POST:
            return

        # Bot username cache
        if not temp.U_NAME:
            me = await client.get_me()
            temp.U_NAME = me.username

        link = f"https://t.me/{temp.U_NAME}?start=avx-{file_unique_id}"

        # Shortlink
        if POST_SHORTLINK:
            try:
                shortlink = await get_shortlink(link)
            except Exception as e:
                print("Shortlink Error:", e)
                shortlink = link
        else:
            shortlink = link

        caption = (
            f"<b>{file_name}</b>\n\n"
            f"<i>Click the button below to watch the video.</i>"
        )

        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("📂 ɢᴇᴛ ᴠɪᴅᴇᴏ 📂", url=shortlink)]
        ])

        # -----------------------
        # THUMBNAIL SYSTEM (FIXED)
        # -----------------------
        thumb_to_send = NO_IMG

        try:
            # 1️⃣ Telegram thumbnail → download → send as photo
            if m.video.thumbs:
                thumb_file = await client.download_media(
                    m.video.thumbs[0].file_id
                )
                if thumb_file:
                    thumb_to_send = thumb_file

            else:
                # 2️⃣ Generate from video
                video_path = await m.download()
                gen_thumb = await generate_thumbnail(video_path)

                if gen_thumb:
                    thumb_to_send = gen_thumb

        except Exception as e:
            print("Thumbnail handling error:", e)

        # -----------------------
        # SEND POST
        # -----------------------
        try:
            await client.send_photo(
                chat_id=POST_CHANNEL,
                photo=thumb_to_send,
                caption=caption,
                reply_markup=btn
            )
            print("📸 Post sent with thumbnail")

        except Exception as e:
            print("⚠️ Thumb failed, sending NO_IMG:", e)
            await client.send_photo(
                chat_id=POST_CHANNEL,
                photo=NO_IMG,
                caption=caption,
                reply_markup=btn
            )

    except Exception as e:
        print(f"❌ Error in Auto Index: {e}")
