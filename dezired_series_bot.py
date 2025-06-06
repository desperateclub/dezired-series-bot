import os
import pickle
import re
import random
import time
from datetime import datetime, timedelta
import telebot
from fuzzywuzzy import process

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it in your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)

# Load scanned data
scanned_data = {}
data_timestamp = {}
if os.path.exists("scanned_data.pkl"):
    try:
        with open("scanned_data.pkl", "rb") as f:
            scanned_data = pickle.load(f)
    except Exception:
        scanned_data = {}

if os.path.exists("timestamp.pkl"):
    try:
        with open("timestamp.pkl", "rb") as f:
            data_timestamp = pickle.load(f)
    except Exception:
        data_timestamp = {}

# Title cleaner
def clean_title(name):
    name = name.lower()
    name = re.sub(
        r'\b(720p|1080p|480p|2160p|4k|x264|x265|bluray|webrip|web-dl|hdrip|dvdrip|hevc|h\.264|h264|h\.265|h265|multi|dubbed|uncut|ddp5\.1|dd5\.1|esub|eng|hin|dual audio|subs?)\b',
        '', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip()

# Fun facts and emojis
fun_facts = [
    "Did you know? 🍿 The first movie ever made was in 1888!",
    "🔥 Fun Fact: The longest film ever made is over 85 hours long!",
    "🎬 Movie magic is real... unless it's Sharknado 😂",
    "😍 Sydney watches all movies... twice. Okay, maybe three times.",
    "🎥 Popcorn is 10x tastier with a good series!"
]

movie_keywords = ["movie", "film"]
series_keywords = ["series", "season", "episode"]

def detect_type(text):
    text = text.lower()
    if any(word in text for word in series_keywords):
        return "series"
    if any(word in text for word in movie_keywords):
        return "movie"
    return None

# Filter messages
ignored_symbols = ['.', '..', '...', ',', '!', '?', '👍', '✌️']

# Greeting/flirty response
@bot.message_handler(func=lambda m: m.text and any(word in m.text.lower() for word in ["hi", "hello", "hey", "sexy", "date", "love"]))
def flirty_reply(message):
    replies = [
        "Hey cutie 😘 What are you watching tonight?",
        "You rang? Sydney’s here 🎬",
        "No dates, only data 🖤 But go on...",
        "Just a bot? Never. I’m *the* Sydney Sweeney 🔥"
    ]
    bot.reply_to(message, random.choice(replies), parse_mode="Markdown")

# Suggestion handler
@bot.message_handler(func=lambda m: m.text and "suggest" in m.text.lower())
def handle_suggestions(message):
    content_type = detect_type(message.text)
    suggestions = []
    for k in scanned_data:
        if content_type == "movie" and not re.search(r's\d+e\d+', k, re.I):
            suggestions.append(k)
        elif content_type == "series" and re.search(r's\d+e\d+', k, re.I):
            suggestions.append(k)
    if suggestions:
        picked = random.sample(suggestions, min(3, len(suggestions)))
        reply = "Here’s something I found just for you:\n\n"
        for title in picked:
            data = scanned_data[title]
            if isinstance(data, list):
                link = data[0]
            else:
                link = data
            reply += f"🎥 *{title}* — [Click here]({link})\n"
        reply += "\n" + random.choice(fun_facts)
        bot.reply_to(message, reply, parse_mode="Markdown")
    else:
        bot.reply_to(message, "Nothing juicy right now 😢 But hang in, I’m on the lookout!")

# Core search response
@bot.message_handler(func=lambda message: message.text and message.text.strip() not in ignored_symbols)
def handle_text(message):
    query = message.text.strip().lower()
    clean_query = clean_title(query)

    content_type = detect_type(query)

    if not scanned_data:
        bot.reply_to(message, "🥲 Nothing in my vault yet. Ask the admins maybe?")
        return

    cleaned_db = {clean_title(k): k for k in scanned_data}
    best_matches = process.extract(clean_query, cleaned_db.keys(), limit=5)

    found = []
    for match, score in best_matches:
        original_title = cleaned_db[match]
        if score >= 65:
            if content_type == "movie" and re.search(r's\d+e\d+', original_title, re.I):
                continue
            if content_type == "series" and not re.search(r's\d+e\d+', original_title, re.I):
                continue
            data = scanned_data[original_title]
            if isinstance(data, list):
                links = "\n".join([f"🔗 [Part {i+1}]({link})" for i, link in enumerate(data)])
            else:
                links = f"🔗 [Click to Download]({data})"
            found.append(f"*{original_title}*\n{links}")

    if found:
        final = "Found these gems for you 💎\n\n" + "\n\n".join(found)
        bot.reply_to(message, final, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Couldn't fetch that. Maybe it's not yet uploaded. Sit tight ❤️")

# File scanning
@bot.message_handler(content_types=["document", "video"])
def scan_file(message):
    file = message.document or message.video
    if not file or not file.file_name:
        return

    file_name = file.file_name
    msg_id = message.message_id
    chat_id = str(message.chat.id)[4:]
    link = f"https://t.me/c/{chat_id}/{msg_id}"

    base_name = clean_title(os.path.splitext(file_name)[0])

    if base_name in scanned_data:
        if isinstance(scanned_data[base_name], list):
            scanned_data[base_name].append(link)
        else:
            scanned_data[base_name] = [scanned_data[base_name], link]
    else:
        scanned_data[base_name] = link

    # Store timestamp for deletion
    data_timestamp[base_name] = time.time()

    # Save files
    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)
    with open("timestamp.pkl", "wb") as f:
        pickle.dump(data_timestamp, f)

# Monitor for pinned messages
@bot.channel_post_handler(content_types=["text"])
def monitor_pinned(message):
    if message.is_automatic_forward:
        return
    if message.pinned:
        bot.reply_to(message, "✨ Featured drop spotted! You don’t wanna miss this one 😍")

# Auto-delete outdated links (Run periodically with a scheduler in production)
def cleanup_old_entries():
    now = time.time()
    expired = [k for k, ts in data_timestamp.items() if now - ts > 86400]
    for k in expired:
        scanned_data.pop(k, None)
        data_timestamp.pop(k, None)
    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)
    with open("timestamp.pkl", "wb") as f:
        pickle.dump(data_timestamp, f)

print("🚀 Sydney Sweeney is live, sassy and scanning 💃")
bot.polling()
