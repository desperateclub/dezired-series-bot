import os
import pickle
import telebot
from fuzzywuzzy import process
import re
import random
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "scanned_data.pkl"
AUTO_DELETE_AFTER = 86400  # 1 day in seconds

# Load scanned data: dict of {title: {"links": [url,...], "timestamp": last_update_epoch}}
scanned_data = {}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "rb") as f:
            scanned_data = pickle.load(f)
    except Exception:
        scanned_data = {}

def save_data():
    with open(DATA_FILE, "wb") as f:
        pickle.dump(scanned_data, f)

def clean_title(name):
    name = name.lower()
    name = re.sub(r'\b(720p|1080p|480p|2160p|4k|x264|x265|bluray|webrip|web-dl|hdrip|dvdrip|hevc|h\.264|h264|h\.265|h265|multi|dubbed|uncut|ddp5\.1|dd5\.1|esub|eng|hin|dual audio|hdrip)\b', '', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip()

movie_keywords = ["movie", "film"]
series_keywords = ["series", "episode", "season"]

def detect_type(text):
    text = text.lower()
    if any(word in text for word in series_keywords):
        return "series"
    if any(word in text for word in movie_keywords):
        return "movie"
    return None

def is_series(title):
    # Simple regex to detect series episodes in title: s01e01 or S1E1 etc.
    return bool(re.search(r's\d+e\d+', title, re.I))

def mood_emoji(title):
    # Basic mood based on movie or series or keywords
    if is_series(title):
        return "📺"
    # Check some keywords for moods
    title_lower = title.lower()
    if any(k in title_lower for k in ["romance", "love", "heart"]):
        return "😍"
    if any(k in title_lower for k in ["action", "fight", "war", "battle"]):
        return "🔥"
    if any(k in title_lower for k in ["comedy", "funny", "laugh", "haha"]):
        return "😂"
    return "🎬"

# Auto delete old links after 1 day
def purge_old_links():
    now = time.time()
    changed = False
    to_del = []
    for title, data in scanned_data.items():
        ts = data.get("timestamp", now)
        if now - ts > AUTO_DELETE_AFTER:
            to_del.append(title)
    for title in to_del:
        del scanned_data[title]
        changed = True
    if changed:
        save_data()

# Ignore messages that are only symbols or very short junk
def is_junk_message(text):
    return text.strip() in {".", "..", "...", ",", "-", "_", "", "!"}

# Sassy replies to greetings or flirts
flirt_keywords = ["hi", "hello", "hey", "beautiful", "sexy", "date", "love"]
@bot.message_handler(func=lambda m: any(w in m.text.lower() for w in flirt_keywords))
def sassy_reply(message):
    if is_junk_message(message.text):
        return
    replies = [
        "Oh hey there 👀 You up to something?",
        "I’m just a bot, but flattered 😏",
        "Sydney’s busy curating 🔥 content. What’s up?",
        "Hehe. Focus on movies, loverboy 💋"
    ]
    bot.reply_to(message, random.choice(replies))

# Main responder
@bot.message_handler(func=lambda m: True, content_types=["text"])
def respond(message):
    purge_old_links()
    text = message.text.strip()
    if is_junk_message(text):
        return

    if not scanned_data:
        bot.reply_to(message, "⚠️ No files added yet, hun. Wait for the admins.")
        return

    content_type = detect_type(text)  # movie or series or None
    search_text = clean_title(text)

    cleaned_db = {clean_title(k): k for k in scanned_data.keys()}

    # 1) Try exact match first (score=100)
    exact_matches = [(title, 100) for title in cleaned_db if title == search_text]

    # 2) If none exact, fallback fuzzy (score >= 60)
    if not exact_matches:
        fuzzy_matches = process.extract(search_text, cleaned_db.keys(), limit=5)
        exact_matches = [(m, s) for m, s in fuzzy_matches if s >= 60]

    results = []
    for match, score in exact_matches:
        original_title = cleaned_db[match]

        # filter type
        if content_type == "movie" and is_series(original_title):
            continue
        if content_type == "series" and not is_series(original_title):
            continue

        data = scanned_data.get(original_title)
        if not data:
            continue

        links = data["links"] if isinstance(data, dict) else data
        if isinstance(links, list):
            links_str = "\n".join([f"🔗 [Part {i+1}]({l})" for i, l in enumerate(links)])
        else:
            links_str = f"🔗 [Click to Download]({links})"

        results.append(f"{mood_emoji(original_title)} *{original_title}*\n{links_str}")

    if results:
        bot.reply_to(message, "Here’s what I found for you, babe 😉\n\n" + "\n\n".join(results), parse_mode="Markdown")
    else:
        bot.reply_to(message, "I didn’t find that one 😔 Check the name or wait for the admins to bless us with it.")

# Handle new files added
@bot.message_handler(content_types=["document", "video"])
def handle_new_file(message):
    file_name = message.document.file_name if message.document else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
    base_name = clean_title(os.path.splitext(file_name)[0])

    now = time.time()
    if base_name in scanned_data:
        # If existing record is dict (links + timestamp)
        if isinstance(scanned_data[base_name], dict):
            scanned_data[base_name]["links"].append(file_link)
            scanned_data[base_name]["timestamp"] = now
        else:
            # convert to dict for new format
            scanned_data[base_name] = {"links": [scanned_data[base_name], file_link], "timestamp": now}
    else:
        scanned_data[base_name] = {"links": [file_link], "timestamp": now}

    save_data()

    # Special treatment for pinned messages if needed could go here
    # You can add logic to detect pinned messages and mark featured content

print("🌀 Sydney Sweeney is online and ready to slay 🎬")
bot.polling()
