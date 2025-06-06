import os
import pickle
import telebot
from fuzzywuzzy import process
import re
import random
import time
from threading import Thread

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it in your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)
scanned_data = {}

# Load scanned data
if os.path.exists("scanned_data.pkl"):
    try:
        with open("scanned_data.pkl", "rb") as f:
            scanned_data = pickle.load(f)
    except Exception:
        scanned_data = {}

# Clean title to ignore resolution, quality etc.
def clean_title(name):
    name = name.lower()
    name = re.sub(r'\b(720p|1080p|480p|2160p|4k|x264|x265|bluray|webrip|web-dl|hdrip|dvdrip|hevc|h\.264|h264|h\.265|h265|multi|dubbed|uncut|ddp5\.1|dd5\.1|esub|eng|hin|dual audio)\b', '', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip()

# Distinguish movies and series
movie_keywords = ["movie", "film"]
series_keywords = ["series", "episode", "season"]
def detect_type(text):
    text = text.lower()
    if any(word in text for word in series_keywords):
        return "series"
    if any(word in text for word in movie_keywords):
        return "movie"
    return None

# Emoji generator based on movie/series type
def emoji_for_title(title):
    if re.search(r'\b(comedy|funny|lol|🤣|😂)\b', title.lower()):
        return "😂"
    elif re.search(r'\b(action|war|battle|spy|mission)\b', title.lower()):
        return "🔥"
    elif re.search(r'\b(romance|love|romcom|❤️|😍)\b', title.lower()):
        return "😍"
    else:
        return "🎬"

# Auto-delete messages older than 1 day (run as background thread)
def cleanup_scanned_data():
    while True:
        changed = False
        now = time.time()
        for title in list(scanned_data.keys()):
            entry = scanned_data[title]
            if isinstance(entry, dict) and 'timestamp' in entry:
                if now - entry['timestamp'] > 86400:  # 1 day
                    del scanned_data[title]
                    changed = True
        if changed:
            with open("scanned_data.pkl", "wb") as f:
                pickle.dump(scanned_data, f)
        time.sleep(3600)

Thread(target=cleanup_scanned_data, daemon=True).start()

# Ignore messages like '.', '..', '...', etc.
symbol_pattern = re.compile(r'^[\s.,!@#$%^&*()_+=\-]{1,5}$')

# Flirty replies
flirt_keywords = ["hi", "hello", "hey", "beautiful", "sexy", "date", "love"]
@bot.message_handler(func=lambda message: any(word in message.text.lower() for word in flirt_keywords))
def handle_flirts(message):
    replies = [
        "Oh hey there 👀 You up to something?",
        "I’m just a bot, but flattered 😏",
        "Sydney’s busy curating 🔥 content. What’s up?",
        "Hehe. Focus on movies, loverboy 💋"
    ]
    bot.reply_to(message, random.choice(replies))

# Main message responder
@bot.message_handler(func=lambda message: True, content_types=["text"])
def respond_to_query(message):
    query = message.text.strip()
    if symbol_pattern.match(query):
        return  # Ignore

    clean_query = clean_title(query)
    if not scanned_data:
        bot.reply_to(message, "⚠️ No files added yet, hun. Wait for the admins.")
        return

    content_type = detect_type(query)

    cleaned_db = {clean_title(k): k for k in scanned_data.keys()}
    best_matches = process.extract(clean_query, cleaned_db.keys(), limit=5)
    matches_with_links = []

    for match, score in best_matches:
        original_title = cleaned_db[match]
        if score >= 60:
            if content_type == "movie" and re.search(r's\d+e\d+', original_title, re.I):
                continue
            if content_type == "series" and not re.search(r's\d+e\d+', original_title, re.I):
                continue
            data = scanned_data[original_title]['link'] if isinstance(scanned_data[original_title], dict) else scanned_data[original_title]
            emoji = emoji_for_title(original_title)

            if isinstance(data, list):
                links = "\n".join([f"🔗 [Part {i+1}]({link})" for i, link in enumerate(data)])
            else:
                links = f"🔗 [Click to Download]({data})"

            matches_with_links.append(f"{emoji} **{original_title}**\n{links}")

    if matches_with_links:
        response = "Here’s what I found for you, babe 😉\n\n" + "\n\n".join(matches_with_links)
        bot.reply_to(message, response, parse_mode="Markdown")
    else:
        bot.reply_to(message, "I didn’t find that one 😔 Check the name or wait for the admins to bless us with it.")

# File uploads
@bot.message_handler(content_types=["document", "video"])
def handle_new_file(message):
    file = message.document or message.video
    if not file:
        return

    file_name = file.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
    base_name = clean_title(os.path.splitext(file_name)[0])

    entry = scanned_data.get(base_name, {})
    if isinstance(entry, dict):
        entry.setdefault("link", []).append(file_link)
        entry["timestamp"] = time.time()
    elif isinstance(entry, list):
        scanned_data[base_name] = {"link": entry + [file_link], "timestamp": time.time()}
    elif entry:
        scanned_data[base_name] = {"link": [entry, file_link], "timestamp": time.time()}
    else:
        scanned_data[base_name] = {"link": file_link, "timestamp": time.time()}

    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)

# Pinned message handler
@bot.message_handler(func=lambda message: message.pinned_message is not None)
def handle_pinned(message):
    bot.reply_to(message, "⭐ Featured content pinned! You better not miss this one 😍")

# Start Sydney
print("🌀 Sydney Sweeney is online and ready to slay 🎬")
bot.polling()
