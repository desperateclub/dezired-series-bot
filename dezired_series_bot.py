import os
import pickle
import time
import random
import re
from datetime import datetime, timezone

import telebot
from telebot import types

from telethon import TelegramClient
from telethon.sessions import StringSession

# Load env from Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# TeleBot setup
bot = telebot.TeleBot(BOT_TOKEN)

# Telethon setup
with open("session_string.txt") as f:
    session_str = f.read().strip()

client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
client.start()

# Chat data store
DATA_FILE = "scanned_data.pkl"
try:
    with open(DATA_FILE, "rb") as f:
        scanned = pickle.load(f)
except:
    scanned = {}

def save_data():
    with open(DATA_FILE, "wb") as f:
        pickle.dump(scanned, f)

def normal(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

def scan_history():
    count = 0
    for msg in client.iter_messages(GROUP_ID, limit=1000):
        if msg.document:
            key = normal(msg.document.file_name)
            ln = f"https://t.me/c/{str(GROUP_ID)[4:]}/{msg.id}"
            scanned.setdefault(key, []).append({
                "name": msg.document.file_name,
                "link": ln,
                "ts": time.time()
            })
            count += 1
    save_data()
    return count

# Command to trigger scanning
@bot.message_handler(commands=["scan_history"])
def handle_scan(m):
    if m.chat.id != GROUP_ID:
        return
    bot.reply_to(m, "🔍 Scanning history, hold on...")
    num = scan_history()
    bot.send_message(GROUP_ID, f"✅ History scanned! {num} files recorded.")

# Search handler
@bot.message_handler(func=lambda m: m.chat.id == GROUP_ID and m.content_type == "text")
def handle_search(m):
    q = m.text.strip()
    if q in {".", "..", "...", ",", "-"}:
        return
    key = normal(q)
    for title, files in scanned.items():
        if key in title:
            lines = [f"{f['name']} → {f['link']}" for f in files]
            bot.reply_to(m, "🎬 Here you go:\n" + "\n".join(lines))
            return
    bot.reply_to(m, f"❌ No match for *{q}*.\nTry running /scan_history", parse_mode="Markdown")

# Start the bot
print("⚡ Sydney Sweeney is online.")
bot.infinity_polling(skip_pending=True)
