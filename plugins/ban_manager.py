import time
from pyrogram.types import Message
from database.users_db import db
from info import LOG_CHANNEL, ADMINS

class BanManager:
    def __init__(self):
        self.FLOOD_LIMIT = 5
        self.TIME_WINDOW = 7
        self.WARNING_LIMIT = 3
        self.user_flood_history = {}
        self.user_warnings = {}
        self.blocked_cache = {}   
        
    async def check_ban(self, client, m: Message):
        user_id = m.from_user.id
        current_time = time.time()
        try:
            if isinstance(ADMINS, list) and user_id in ADMINS:
                return False
            if isinstance(ADMINS, int) and user_id == ADMINS:
                return False
        except:
            pass
        if self.blocked_cache.get(user_id):
            await self._send_block_msg(m)
            return True
        is_blocked = await db.is_user_blocked(user_id)
        if is_blocked:
            self.blocked_cache[user_id] = True
            await self._send_block_msg(m)
            return True
        is_temp_banned, remaining = await db.is_temp_banned(user_id)
        if is_temp_banned:
            await m.reply(
                f"🚫 <b>You are temporarily banned!</b>\n\n⏳ Wait: <code>{remaining}s</code>"
            )
            return True
        history = self.user_flood_history.setdefault(user_id, [])
        history.append(current_time)
        history[:] = [t for t in history if current_time - t < self.TIME_WINDOW]
        if len(history) >= self.FLOOD_LIMIT:
            await self.punish_user(client, m, user_id)
            self.user_flood_history[user_id] = []
            return True
        return False

    async def punish_user(self, client, m: Message, user_id: int):
        self.user_warnings[user_id] = self.user_warnings.get(user_id, 0) + 1
        warn_count = self.user_warnings[user_id]
        user_link = m.from_user.mention

        try:
            await m.delete()
        except:
            pass

        if warn_count == 1:
            await m.reply("⚠ <b>Warning 1/3:</b> Stop spamming!")
            await client.send_message(LOG_CHANNEL, f"⚠️ #Spam_Warn_1\n👤 {user_link}\n🆔 {user_id}")

        elif warn_count == 2:
            await m.reply("⚠ <b>Warning 2/3:</b> LAST WARNING!")

        elif warn_count == 3:
            await db.add_temp_ban(user_id, 600)
            await m.reply("🚫 <b>Spam Detected!</b>\n\nYou are banned for 10 Minutes.")
            await client.send_message(LOG_CHANNEL, f"🟡 #Temp_Ban_10m\n👤 {user_link}\n🆔 {user_id}")

        elif warn_count == 4:
            await db.add_temp_ban(user_id, 3600)
            await m.reply("🚫 <b>Repeat Offender!</b>\n\nYou are banned for 1 Hour.")

        elif warn_count >= 5:
            await db.block_user(user_id, reason="Auto-Ban: Excessive Spam")
            self.blocked_cache[user_id] = True
            await m.reply("🛑 <b>Permanent Ban!</b>\n\nGoodbye.")
            await client.send_message(LOG_CHANNEL, f"🛑 #Perm_Ban\n👤 {user_link}\n🆔 {user_id}")

    async def _send_block_msg(self, m: Message):
        try:
            await m.reply("❌ 𝘠𝘰𝘶 𝘢𝘳𝘦 𝘣𝘭𝘰𝘤𝘬𝘦𝘥 𝘧𝘳𝘰𝘮 𝘶𝘴𝘪𝘯𝘨 𝘵𝘩𝘪𝘴 𝘣𝘰𝘵..")
        except:
            pass


# 🔹 Initialize
ban_manager = BanManager()
