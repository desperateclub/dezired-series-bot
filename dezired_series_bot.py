import os
import pickle
import telebot
from fuzzywuzzy import process
import re
import random
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing.")

bot = telebot.TeleBot(BOT_TOKEN)
DELETE_THRESHOLD = 86400  # 24 hours in seconds

scanned_data = {}
if os.path.exists("scanned_data.pkl"):
    try:
        with open("scanned_data.pkl", "rb") as f:
            scanned_data = pickle.load(f)
    except Exception:
        scanned_data = {}

def clean_title(name):
    name = name.lower()
    name = re.sub(r'\b(720p|1080p|480p|2160p|4k|x264|x265|bluray|webrip|web-dl|hdrip|dvdrip|hevc|h\.264|h264|h\.265|h265|multi|dubbed|uncut|ddp5\.1|dd5\.1|esub|eng|hin|dual audio)\b', '', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip()

movie_keywords = ["movie", "film"]
series_keywords = ["series", "episode", "season"]

def detect_type(text):
    text = text.lower()
    if any(w in text for w in series_keywords): 
        return "series"
    if any(w in text for w in movie_keywords): 
        return "movie"
    return None

flirt_keywords = ["hi", "hello", "hey", "beautiful", "sexy", "date", "love"]
@bot.message_handler(func=lambda m: any(w in m.text.lower() for w in flirt_keywords))
def flirt_reply(message):
    responses = [
        "Oh hey there 👀 You up to something?",
        "I’m just a bot, but flattered 😏",
        "Sydney’s busy curating 🔥 content. What’s up?",
        "Hehe. Focus on movies, loverboy 💋"
    ]
    bot.reply_to(message, random.choice(responses))

def mood_emoji(title):
    title = title.lower()
    if any(k in title for k in ["love", "romance", "kiss"]):
        return "😍"
    if any(k in title for k in ["funny", "comedy", "laugh"]):
        return "😂"
    return "🔥"

def is_series(name):
    return bool(re.search(r's\d+e\d+', name, re.I))

def purge_old_links():
    now = time.time()
    to_delete = []
    for title, info in scanned_data.items():
        if isinstance(info, dict):
            if now - info.get("timestamp", 0) > DELETE_THRESHOLD:
                to_delete.append(title)
    for title in to_delete:
        del scanned_data[title]

@bot.message_handler(func=lambda m: True, content_types=["text"])
def respond(message):
    purge_old_links()
    text = message.text.strip()

    # Ignore messages that are just symbols
    if text in {".", "..", "...", ",", "-", "_"}:
        return

    # If scanned_data empty
    if not scanned_data:
        bot.reply_to(message, "⚠️ No files added yet, hun. Wait for the admins.")
        return

    # Detect if user wants movie or series or neither explicitly
    content_type = detect_type(text)
    # Clean the search text for fuzzy matching
    search_text = clean_title(text)

    cleaned_db = {clean_title(k): k for k in scanned_data.keys()}
    matches = process.extract(search_text, cleaned_db.keys(), limit=5)

    results = []
    for match, score in matches:
        if score < 60:
            continue
        original_title = cleaned_db[match]

        # Skip series if user wants movie, and vice versa
        if content_type == "movie" and is_series(original_title):
            continue
        if content_type == "series" and not is_series(original_title):
            continue

        data = scanned_data[original_title]
        links = data["link"] if isinstance(data, dict) else data
        if isinstance(links, list):
            links_str = "\n".join([f"🔗 [Part {i+1}]({l})" for i, l in enumerate(links)])
        else:
            links_str = f"🔗 [Click to Download]({links})"
        results.append(f"{mood_emoji(original_title)} *{original_title}*\n{links_str}")

    if results:
        bot.reply_to(message, "Here’s what I found for you, babe 😉\n\n" + "\n\n".join(results), parse_mode="Markdown")
    else:
        bot.reply_to(message, "I didn’t find that one 😔 Check the name or wait for the admins to bless us with it.")

@bot.message_handler(content_types=["document", "video"])
def handle_new_file(message):
    file_name = message.document.file_name if message.content_type == "document" else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
    base_name = clean_title(os.path.splitext(file_name)[0])

    data = {
        "link": file_link,
        "timestamp": time.time(),
        "pinned": getattr(message, "pinned", False)
    }

    if base_name in scanned_data:
        existing = scanned_data[base_name]
        if isinstance(existing["link"], list):
            existing["link"].append(file_link)
        else:
            existing["link"] = [existing["link"], file_link]
        existing["timestamp"] = time.time()
    else:
        scanned_data[base_name] = data

    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)

    if getattr(message, "pinned", False):
        bot.reply_to(message, "⭐ Featured content added to Dezired Series!")

print("🌀 Sydney Sweeney is online and ready to slay 🎬")
bot.polling()
