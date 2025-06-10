import os
import json
import re
import time
import random
import telebot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
DATA_FILE = "scanned_data.json"

bot = telebot.TeleBot(BOT_TOKEN)

# Load scanned data
try:
    with open(DATA_FILE, "r") as f:
        scanned_data = json.load(f)
except FileNotFoundError:
    scanned_data = {}

# Helper to normalize text
def normalize(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

# 🔍 Manual history scan using Telethon
@bot.message_handler(commands=["scan_history"])
def do_scan_history(message):
    if message.chat.id != GROUP_ID:
        bot.reply_to(message, "⛔️ This command only works in the group.")
        return

    msg = bot.reply_to(message, "⏳ Scanning group history... This may take a while.")
    os.system("python3 telethon_scanner.py")

    # Reload scanned data after scan
    global scanned_data
    try:
        with open(DATA_FILE, "r") as f:
            scanned_data = json.load(f)
        bot.edit_message_text("✅ History scan complete. You can now search!", message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Failed to load scan data.\n{str(e)}", message.chat.id, msg.message_id)

# 🎯 Main search logic
@bot.message_handler(func=lambda msg: msg.chat.id == GROUP_ID and msg.content_type == "text")
def search_file(message):
    query = message.text.strip()
    if not query or len(query) < 2 or query.startswith(("/", ".")):
        return

    normalized_query = normalize(query)

    for title, info in scanned_data.items():
        if normalized_query in normalize(title):
            link = f"https://t.me/c/{str(GROUP_ID)[4:]}/{info['message_id']}"
            bot.reply_to(message, f"🎬 *{info['file_name']}*\n🔗 {link}", parse_mode="Markdown")
            return

    bot.reply_to(message, f"❌ *{query}* not found. Try /scan_history if files were recently uploaded.", parse_mode="Markdown")

print("🔥 Sydney Sweeney is online and serving sass 🎬")
bot.infinity_polling(skip_pending=True)
