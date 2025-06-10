from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os

session_string = os.getenv("SESSION_STRING")
api_id = int(os.getenv("API_ID"))  # set this in Railway
api_hash = os.getenv("API_HASH")   # set this in Railway

telethon_client = TelegramClient(StringSession(session_string), api_id, api_hash)

import os, json, re, random
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
DATA_FILE = "scanned_data.json"
bot = telebot.TeleBot(BOT_TOKEN)

try:
    with open(DATA_FILE) as f:
        scanned_data = json.load(f)
except:
    scanned_data = {}

normalize = lambda t: re.sub(r'[^a-z0-9]', '', t.lower())

@bot.message_handler(commands=["scan_history"])
def cmd_scan(m):
    if m.chat.id != GROUP_ID: return
    msg = bot.reply_to(m, "🔍 Scanning group history...")
    os.system("python3 telethon_scanner.py")
    try:
        with open(DATA_FILE) as f:
            global scanned_data
            scanned_data = json.load(f)
        bot.send_message(GROUP_ID, f"✅ Scan complete. {len(scanned_data)} files recorded.")
    except:
        bot.edit_message_text("❌ Scan failed.", GROUP_ID, msg.message_id)

@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID and m.content_type == "text")
def search(m):
    q = m.text.strip()
    if not q or q.startswith((".", "/", "..")): return
    key = normalize(q)
    for title, info in scanned_data.items():
        if key in normalize(title):
            ln = f"https://t.me/c/{str(GROUP_ID)[4:]}/{info['message_id']}"
            emoji = random.choice(["🔥","😂","🎬"])
            bot.reply_to(m, f"{emoji} *{info['file_name']}*\n🔗 {ln}", parse_mode="Markdown", disable_web_page_preview=True)
            return
    bot.reply_to(m, f"❌ *{q}* not found. Try /scan_history first!", parse_mode="Markdown")

print("⚡ Sydney Sweeney is online.")
bot.infinity_polling(skip_pending=True)
