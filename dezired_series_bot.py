import os
import pickle
import telebot
from fuzzywuzzy import process
import re
import random
import time
from datetime import datetime, timedelta

# --- Bot setup ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing in environment variables.")
bot = telebot.TeleBot(BOT_TOKEN)

# --- Load scanned data ---
scanned_data = {}
if os.path.exists("scanned_data.pkl"):
    try:
        with open("scanned_data.pkl", "rb") as f:
            scanned_data = pickle.load(f)
    except Exception:
        scanned_data = {}

# --- Clean title ---
def clean_title(name):
    name = name.lower()
    name = re.sub(r'\b(720p|1080p|480p|2160p|4k|x264|x265|bluray|webrip|web-dl|hdrip|dvdrip|hevc|h\.264|h264|h\.265|h265|multi|dubbed|uncut|ddp5\.1|dd5\.1|esub|eng|hin|dual audio)\b', '', name)
    name = re.sub(r'[^a-z0-9\s]', ' ', name)
    return re.sub(r'\s+', ' ', name).strip()

# --- Detect type ---
movie_keywords = ["movie", "film"]
series_keywords = ["series", "episode", "season"]
def detect_type(text):
    text = text.lower()
    if any(word in text for word in series_keywords):
        return "series"
    if any(word in text for word in movie_keywords):
        return "movie"
    return None

# --- Avoid symbol-only triggers ---
def is_valid_query(text):
    return bool(re.search(r'[a-zA-Z0-9]', text.strip()))

# --- Fun/flirt handler ---
@bot.message_handler(func=lambda m: any(w in m.text.lower() for w in ["hi", "hello", "hey", "sexy", "beautiful", "babe", "love", "date"]))
def flirt_reply(message):
    replies = [
        "Oh hey there 😘 Looking for something hot?",
        "Sydney's here, what are we watching today? 🎬",
        "Careful now, I'm not just a pretty face 😉",
        "Stop flirting, start streaming 😏",
    ]
    bot.reply_to(message, random.choice(replies))

# --- Fun facts ---
fun_facts = [
    "🎬 Did you know? The first feature film ever made was 'The Story of the Kelly Gang' in 1906!",
    "📺 Fun fact: The most-watched TV episode ever is the M*A*S*H finale!",
    "🍿 Popcorn became popular in theaters during the Great Depression. Cheap and crunchy!",
    "🎥 Sydney loves a good plot twist. Just like your love life 💔➡️❤️",
]

# --- Message handler ---
@bot.message_handler(func=lambda m: m.text and is_valid_query(m.text), content_types=["text"])
def handle_message(message):
    query = message.text.strip().lower()
    clean_query = clean_title(query)
    content_type = detect_type(query)

    if not scanned_data:
        bot.reply_to(message, "⚠️ I’ve got no files in my closet yet, hun. Wait for the admins 😪")
        return

    # Matching
    cleaned_db = {clean_title(k): k for k in scanned_data.keys()}
    best_matches = process.extract(clean_query, cleaned_db.keys(), limit=5)
    matches_with_links = []

    for match, score in best_matches:
        original_title = cleaned_db[match]
        if score >= 70:
            # Filter by content type
            is_series = bool(re.search(r's\d+e\d+', original_title, re.I))
            if content_type == "movie" and is_series:
                continue
            if content_type == "series" and not is_series:
                continue

            file_info = scanned_data[original_title]
            file_time = file_info.get("timestamp")
            if file_time and datetime.now().timestamp() - file_time > 86400:
                continue  # skip expired

            links = file_info["links"]
            if len(links) > 1:
                master_link = links[0]
                part_links = "\n".join([f"🔹 [Part {i+1}]({link})" for i, link in enumerate(links)])
                result = f"🎬 **{original_title}**\n📌 [Master Link]({master_link})\n{part_links}"
            else:
                result = f"🎬 **{original_title}**\n🔗 [Click to Download]({links[0]})"

            matches_with_links.append(result)

    if matches_with_links:
        mood = random.choice(["🔥", "😍", "😂", "😈", "🍿"])
        reply = f"{mood} Here's what I found for you, sweetheart:\n\n" + "\n\n".join(matches_with_links)
        if random.random() < 0.3:
            reply += f"\n\n💡 {random.choice(fun_facts)}"
        bot.reply_to(message, reply, parse_mode="Markdown")
    else:
        bot.reply_to(message, "🥲 Couldn’t find it. Check the name or let the admins drop it soon.")

# --- Handle new files ---
@bot.message_handler(content_types=["document", "video"])
def handle_new_file(message):
    file_name = message.document.file_name if message.document else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
    title = clean_title(os.path.splitext(file_name)[0])

    if title in scanned_data:
        scanned_data[title]["links"].append(file_link)
    else:
        scanned_data[title] = {
            "links": [file_link],
            "timestamp": time.time()
        }

    # Save
    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)

# --- Start the bot ---
print("🔥 Sydney Sweeney is online and serving sass 🎬")
bot.polling(non_stop=True)
