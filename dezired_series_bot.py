import os
import pickle
import time
import re
import random
from datetime import datetime, timezone
import telebot
from telebot.types import Message

TOKEN = os.getenv("BOT_TOKEN")         # Set this in Railway
GROUP_ID = int(os.getenv("GROUP_ID")) # e.g. -1001612892172

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "scanned_data.pkl"

# Load existing data
try:
    with open(DATA_FILE, "rb") as f:
        scanned_data = pickle.load(f)
except:
    scanned_data = {}

# Ignore these
ignore_q = {".", "..", "...", ",", "-", "_"}

def save_data():
    with open(DATA_FILE, "wb") as f:
        pickle.dump(scanned_data, f)

def safe_text(txt):
    return re.sub(r'[^a-z0-9]', '', txt.lower())

def clean_title(fn):
    return safe_text(os.path.splitext(fn)[0])

def purge_old():
    now = time.time()
    for title in list(scanned_data.keys()):
        files = scanned_data[title]
        files = [f for f in files if now - f["ts"] < 86400]
        if files: scanned_data[title] = files
        else: scanned_data.pop(title)
    save_data()

@bot.message_handler(commands=["scan_history"])
def do_scan_history(m: Message):
    if m.chat.id != GROUP_ID:
        return
    count = 0
    for msg in bot.get_chat_history(GROUP_ID, limit=500):
        if msg.document:
            key = clean_title(msg.document.file_name)
            link = f"https://t.me/c/{str(GROUP_ID)[4:]}/{msg.message_id}"
            entry = {"fn": msg.document.file_name, "link": link, "ts": time.time()}
            scanned_data.setdefault(key, []).append(entry)
            count += 1
    save_data()
    bot.reply_to(m, f"✅ Scanned {count} files from history.")

@bot.message_handler(commands=["start"])
def hello(m: Message):
    bot.reply_to(m, "Hey, I'm Sydney Sweeney 🍿 — Drop a movie or series name, I'll find it!")

@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID and m.content_type=="text")
def search(m: Message):
    q = m.text.strip()
    if q in ignore_q:
        return
    purge_old()
    sq = safe_text(q)
    for title, files in scanned_data.items():
        if sq in title:
            # Build response
            lines = []
            master = files[0]["link"]
            lines.append(f"🧲 **Master Link:** {master}")
            for i, f in enumerate(files[1:], 2):
                lines.append(f"• Part {i}: {f['link']}")
            emoji = "🔥" if "action" in title else random.choice(["😍","😂","🎥"])
            response = f"{emoji} *Found:* {files[0]['fn']}\n" + "\n".join(lines)
            bot.reply_to(m, response, parse_mode="Markdown", disable_web_page_preview=True)
            return
    bot.reply_to(m, f"❌ Couldn't find *{q}*. Try again or run /scan_history?", parse_mode="Markdown")

bot.infinity_polling(skip_pending=True)
