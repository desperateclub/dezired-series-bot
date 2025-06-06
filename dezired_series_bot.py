import os
import pickle
import telebot
from fuzzywuzzy import process
import re
import random
import time

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it in your environment variables.")
bot = telebot.TeleBot(BOT_TOKEN)

# Auto-delete threshold (24 hrs)
DELETE_THRESHOLD = 86400

# Load scanned data
scanned_data = {}
if os.path.exists("scanned_data.pkl"):
    try:
        with open("scanned_data.pkl", "rb") as f:
            scanned_data = pickle.load(f)
    except Exception:
        scanned_data = {}

# Clean titles (remove quality/resolution tags etc.)
def clean_title(name):
    name = name.lower()
    name = re.sub(r'\b(720p|1080p|480p|2160p|4k|x264|x265|bluray|webrip|web-dl|hdrip|dvdrip|hevc|h\.264|h264|h\.265|h265|multi|dubbed|uncut|ddp5\.1|dd5\.1|esub|eng|hin|dual audio)\b', '', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip()

# Determine type from query
movie_keywords = ["movie", "film"]
series_keywords = ["series", "episode", "season"]
def detect_type(text):
    text = text.lower()
    if any(w in text for w in series_keywords): return "series"
    if any(w in text for w in movie_keywords): return "movie"
    return None

# Flirty / greetings
flirt_keywords = ["hi", "hello", "hey", "beautiful", "sexy", "date", "love"]
@bot.message_handler(func=lambda msg: any(w in msg.text.lower() for w in flirt_keywords))
def flirt_reply(message):
    responses = [
        "Oh hey there 👀 You up to something?",
        "I’m just a bot, but flattered 😏",
        "Sydney’s busy curating 🔥 content. What’s up?",
        "Hehe. Focus on movies, loverboy 💋"
    ]
    bot.reply_to(message, random.choice(responses))

# Detect intent + title
def detect_intent_and_title(text):
    text = text.lower().strip()

    if text in [".", "..", "...", ",", "-", "_"]:
        return {"intent": "ignore"}

    if "suggest" in text:
        if "movie" in text:
            return {"intent": "suggest", "type": "movie"}
        elif "series" in text:
            return {"intent": "suggest", "type": "series"}
        elif "random" in text:
            return {"intent": "suggest", "type": "any"}
        return {"intent": "suggest", "type": None}

    patterns = [r"where is (.+)", r"i want (.+)", r"get me (.+)", r"find (.+)", r"give me (.+)", r"looking for (.+)"]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return {"intent": "search", "title": m.group(1)}
    return {"intent": "search", "title": text}

# Auto-delete old links
def purge_old_links():
    now = time.time()
    to_delete = []
    for title, info in scanned_data.items():
        if isinstance(info, dict):
            if now - info["timestamp"] > DELETE_THRESHOLD:
                to_delete.append(title)
    for key in to_delete:
        del scanned_data[key]

# Emojis
def mood_emoji(title):
    title = title.lower()
    if any(k in title for k in ["love", "romance", "kiss"]):
        return "😍"
    if any(k in title for k in ["funny", "comedy", "laugh"]):
        return "😂"
    return "🔥"

# Handle text messages
@bot.message_handler(func=lambda message: True, content_types=["text"])
def respond(message):
    purge_old_links()
    query = message.text.strip()
    intent_data = detect_intent_and_title(query)

    if intent_data.get("intent") == "ignore":
        return

    content_type = intent_data.get("type")
    title_to_search = intent_data.get("title")

    cleaned_db = {clean_title(k): k for k in scanned_data.keys()}

    def is_series(name):
        return bool(re.search(r's\d+e\d+', name, re.I))

    if intent_data["intent"] == "suggest":
        choices = []
        for k in scanned_data:
            if content_type == "movie" and not is_series(k):
                choices.append(k)
            elif content_type == "series" and is_series(k):
                choices.append(k)
            elif content_type == "any":
                choices.append(k)
        if choices:
            selected = random.choice(choices)
            data = scanned_data[selected]
            if isinstance(data["link"], list):
                links = "\n".join([f"🔗 [Part {i+1}]({l})" for i, l in enumerate(data["link"])])
            else:
                links = f"🔗 [Click to Download]({data['link']})"
            bot.reply_to(message, f"{mood_emoji(selected)} Try this one: *{selected}*\n{links}", parse_mode="Markdown")
        else:
            bot.reply_to(message, "😔 Sorry babe, nothing to suggest right now.")
        return

    if intent_data["intent"] == "search" and title_to_search:
        cleaned_query = clean_title(title_to_search)
        best_matches = process.extract(cleaned_query, cleaned_db.keys(), limit=5)
        matches = []

        for match, score in best_matches:
            orig_title = cleaned_db[match]
            if score >= 60:
                if content_type == "movie" and is_series(orig_title):
                    continue
                if content_type == "series" and not is_series(orig_title):
                    continue
                data = scanned_data[orig_title]
                if isinstance(data["link"], list):
                    links = "\n".join([f"🔗 [Part {i+1}]({l})" for i, l in enumerate(data["link"])])
                else:
                    links = f"🔗 [Click to Download]({data['link']})"
                matches.append(f"{mood_emoji(orig_title)} *{orig_title}*\n{links}")

        if matches:
            bot.reply_to(message, "Here’s what I found for you, babe 😉\n\n" + "\n\n".join(matches), parse_mode="Markdown")
        else:
            bot.reply_to(message, "I didn’t find that one 😔 Check the name or wait for the admins to bless us with it.")

# Save files
@bot.message_handler(content_types=["document", "video"])
def handle_new_file(message):
    file_name = message.document.file_name if message.document else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
    base_name = clean_title(os.path.splitext(file_name)[0])

    data = {
        "link": file_link,
        "timestamp": time.time(),
        "pinned": message.pinned
    }

    if base_name in scanned_data:
        if isinstance(scanned_data[base_name]["link"], list):
            scanned_data[base_name]["link"].append(file_link)
        else:
            scanned_data[base_name]["link"] = [scanned_data[base_name]["link"], file_link]
    else:
        scanned_data[base_name] = data

    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)

    if message.pinned:
        bot.reply_to(message, "⭐ Featured content added to Dezired Series!")

# Start her engine 💅
print("🌀 Sydney Sweeney is online and ready to slay 🎬")
bot.polling()
