import os
import pickle
import telebot
from fuzzywuzzy import process
import re
import random
from datetime import datetime, timedelta

# Load environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it in your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)

# Load scanned data
scanned_data = {}
if os.path.exists("scanned_data.pkl"):
    try:
        with open("scanned_data.pkl", "rb") as f:
            scanned_data = pickle.load(f)
    except Exception:
        scanned_data = {}

# Clean title for matching
def clean_title(name):
    name = name.lower()
    name = re.sub(r'\b(720p|1080p|480p|2160p|4k|x264|x265|bluray|webrip|web-dl|hdrip|dvdrip|hevc|h\.264|h264|h\.265|h265|multi|dubbed|uncut|ddp5\.1|dd5\.1|esub|eng|hin|dual audio)\b', '', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip()

# Detect content type
movie_keywords = ["movie", "film"]
series_keywords = ["series", "episode", "season"]

def detect_type(text):
    text = text.lower()
    if any(word in text for word in series_keywords):
        return "series"
    if any(word in text for word in movie_keywords):
        return "movie"
    return None

# Detect flirty greetings
flirt_keywords = ["hi", "hello", "hey", "beautiful", "sexy", "date", "love"]
@bot.message_handler(func=lambda message: message.text.lower().strip() in flirt_keywords)
def handle_flirts(message):
    replies = [
        "Oh hey there 👀 You up to something?",
        "I’m just a bot, but flattered 😏",
        "Sydney’s busy curating 🔥 content. What’s up?",
        "Hehe. Focus on movies, loverboy 💋"
    ]
    bot.reply_to(message, random.choice(replies))

# Handle regular messages
@bot.message_handler(func=lambda message: True, content_types=["text"])
def respond_to_query(message):
    query = message.text.strip().lower()
    clean_query = clean_title(query)

    # Skip plain symbols
    if clean_query in [".", ",", "..", "..."]:
        return

    if not scanned_data:
        bot.reply_to(message, "⚠️ No files added yet, hun. Wait for the admins.")
        return

    content_type = detect_type(query)

    # Debug
    print(f"User Query: {query}")
    print(f"Cleaned Query: {clean_query}")
    print(f"Available Files: {list(scanned_data.keys())}")

    cleaned_db = {}
    for original_title in scanned_data:
        cleaned = clean_title(original_title)
        cleaned_db[cleaned] = original_title

    best_matches = process.extract(clean_query, list(cleaned_db.keys()), limit=5)
    matches_with_links = []

    for match, score in best_matches:
        original_title = cleaned_db[match]
        if score >= 60:
            if content_type == "movie" and re.search(r's\d+e\d+', original_title, re.I):
                continue
            if content_type == "series" and not re.search(r's\d+e\d+', original_title, re.I):
                continue

            file_info = scanned_data[original_title]
            links = ""
            if isinstance(file_info, list):
                links = "\n".join([f"🔗 [Part {i+1}]({info['link']})" for i, info in enumerate(file_info)])
                master_link = file_info[0]['link']
                links = f"🧲 [Master Link]({master_link})\n" + links
            elif isinstance(file_info, dict):
                links = f"🔗 [Click to Download]({file_info['link']})"

            matches_with_links.append(f"🎬 **{original_title}**\n{links}")

    if matches_with_links:
        response = "Here’s what I found for you, babe 😉\n\n" + "\n\n".join(matches_with_links)
        bot.reply_to(message, response, parse_mode="Markdown")
    else:
        bot.reply_to(message, "I didn’t find that one 😔 Check the name or wait for the admins to bless us with it.")

# Handle file uploads
@bot.message_handler(content_types=["document", "video"])
def handle_new_file(message):
    file_name = message.document.file_name if message.document else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
    timestamp = datetime.utcnow().timestamp()

    base_name = clean_title(os.path.splitext(file_name)[0])
    file_entry = {"link": file_link, "timestamp": timestamp}

    if base_name in scanned_data:
        if isinstance(scanned_data[base_name], list):
            scanned_data[base_name].append(file_entry)
        else:
            scanned_data[base_name] = [scanned_data[base_name], file_entry]
    else:
        scanned_data[base_name] = file_entry

    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)

# Auto-delete old entries (1 day)
def purge_old_data():
    now = datetime.utcnow().timestamp()
    updated_data = {}
    for k, v in scanned_data.items():
        if isinstance(v, list):
            new_list = [item for item in v if now - item["timestamp"] < 86400]
            if new_list:
                updated_data[k] = new_list
        elif isinstance(v, dict) and now - v["timestamp"] < 86400:
            updated_data[k] = v
    return updated_data

# Purge periodically before polling
scanned_data = purge_old_data()

print("🔥 Sydney Sweeney is online and serving sass 🎬")
bot.polling(non_stop=True)
