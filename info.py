import re
from os import environ

# -------------------------
# Helper
# -------------------------
def str_to_bool(val, default=False):
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes", "on")

# =========================================================
# 🤖 BOT BASIC INFORMATION
# =========================================================
API_ID = int(environ.get("API_ID", "21687889"))
API_HASH = environ.get("API_HASH", "25b60b19b1421d32254db6823bff9c6c")
BOT_TOKEN = environ.get("BOT_TOKEN", "")
PORT = int(environ.get("PORT", "8080"))
TIMEZONE = environ.get("TIMEZONE", "Asia/Kolkata")
OWNER_USERNAME = environ.get("OWNER_USERNAME", "Wetsdream_bot")

# =========================================================
# 💾 DATABASE CONFIGURATION
# =========================================================
DB_URL = environ.get("DATABASE_URI", "mongodb+srv://dasniru929:dasniru123@cluster0.51p5e.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = environ.get("DATABASE_NAME", "EliteBotz")

# =========================================================
# 📢 CHANNELS & ADMINS
# =========================================================
ADMINS = int(environ.get("ADMINS", "7294981090"))

LOG_CHANNEL = int(environ.get("LOG_CHANNEL", "-1003510781325"))
PREMIUM_LOGS = int(environ.get("PREMIUM_LOGS", "-1003510781325"))
VERIFIED_LOG = int(environ.get("VERIFIED_LOG", "-1003510781325"))

POST_CHANNEL = int(environ.get("POST_CHANNEL", "-1003542489377"))
VIDEO_CHANNEL = int(environ.get("VIDEO_CHANNEL", "-1003542489377"))
BRAZZER_CHANNEL = int(environ.get("BRAZZER_CHANNEL", "-1003542489377"))

# Auth channels list
auth_channel_str = environ.get("AUTH_CHANNEL", "-1003520442258")
AUTH_CHANNEL = [int(x) for x in auth_channel_str.split() if x.strip().lstrip("-").isdigit()]

# =========================================================
# ⚙️ FEATURES & TOGGLES  (FIXED)
# =========================================================
FSUB = str_to_bool(environ.get("FSUB"), True)
IS_VERIFY = str_to_bool(environ.get("IS_VERIFY"), False)
POST_SHORTLINK = str_to_bool(environ.get("POST_SHORTLINK"), False)
SEND_POST = str_to_bool(environ.get("SEND_POST"), False)

# =========================================================
# 🔢 LIMITS
# =========================================================
DAILY_LIMIT = int(environ.get("DAILY_LIMIT", "5"))
VERIFICATION_DAILY_LIMIT = int(environ.get("VERIFICATION_DAILY_LIMIT", "20"))
PREMIUM_DAILY_LIMIT = int(environ.get("PREMIUM_DAILY_LIMIT", "50"))

# =========================================================
# 🔗 SHORTLINK & VERIFICATION
# =========================================================
SHORTLINK_URL = environ.get("SHORTLINK_URL", "")
SHORTLINK_API = environ.get("SHORTLINK_API", "")
POST_SHORTLINK_URL = environ.get("POST_SHORTLINK_URL", "")
POST_SHORTLINK_API = environ.get("POST_SHORTLINK_API", "")
VERIFY_EXPIRE = int(environ.get("VERIFY_EXPIRE", "3600"))
TUTORIAL_LINK = environ.get("TUTORIAL_LINK", "")

# =========================================================
# 💳 PAYMENT SETTINGS
# =========================================================
UPI_ID = environ.get("UPI_ID", "keshavstutiguriya-1@oksbi")
QR_CODE_IMAGE = environ.get("QR_CODE_IMAGE", "https://indicamps.in/uploads/file_257.jpg")

# =========================================================
# 🖼️ IMAGES
# =========================================================
START_PIC = environ.get("START_PIC", "")
AUTH_PICS = environ.get("AUTH_PICS", "")
VERIFY_IMG = environ.get("VERIFY_IMG", "")
NO_IMG = environ.get("NO_IMG", "")

# =========================================================
# 🌐 WEB APP
# =========================================================
WEB_APP_URL = environ.get("WEB_APP_URL", "")
