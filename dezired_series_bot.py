import os
import pickle
import telebot
from fuzzywuzzy import process
import re
import random
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it as an environment variable.")

bot = telebot.TeleBot(BOT_TOKEN)

# Load data
scanned_data = {}
timestamp_data = {}
if os.path.exists("scanned_data.pkl"):
    with open("scanned_data.pkl", "rb") as f:
        scanned_data = pickle.load(f)

if os.path.exists("timestamp_data.pkl"):
    with open("timestamp_data.pkl", "rb") as f:
        timestamp_data = pickle.load(f)

# Clean titles
def clean_title(name):
    name = name.lower()
    name = re.sub(r'\b(720p|1080p|480p|4k|x264|x265|bluray|webrip|web-dl|hdrip|dvdrip|hevc|h264|h265|multi|dubbed|uncut|ddp5\.1|dd5\.1|esub|eng|hin|dual audio)\b', '', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip()

# Delete old entries after 1 day
def clean_old_entries():
    now = datetime.now()
    expired = [title for title, ts in timestamp_data.items() if now - ts > timedelta(days=1)]
    for title in expired:
        scanned_data.pop(title, None)
        timestamp_data.pop(title, None)

    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)
    with open("timestamp_data.pkl", "wb") as f:
        pickle.dump(timestamp_data, f)

clean_old_entries()

# Flirt/fun replies
flirt_keywords = ["hi", "hello", "hey", "sexy", "date", "beautiful", "love"]
flirty_responses = [
    "Oh hey there 😘 Looking for a movie or love?",
    "Sydney's here, hotter than your last crush 🔥",
    "You talkin' to me? 😉",
    "Hehe, stop flirting and pick a movie loverboy 💋",
]

@bot.message_handler(func=lambda m: any(w in m.text.lower() for w in flirt_keywords))
def flirt_reply(message):
    bot.reply_to(message, random.choice(flirty_responses))

# Skip symbol-only messages
@bot.message_handler(func=lambda msg: msg.text.strip() in [".", ",", "..", "..."])
def ignore_symbols(msg):
    return

# Handle movie/series search
@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_search(message):
    query = clean_title(message.text)
    if not scanned_data:
        bot.reply_to(message, "Nothing’s here yet, darling 😢 Ask admins to upload some movies.")
        return

    matches = process.extract(query, [clean_title(t) for t in scanned_data.keys()], limit=5)
    response = []
    for match, score in matches:
        if score < 70:
            continue
        original_title = next((k for k in scanned_data if clean_title(k) == match), None)
        if not original_title:
            continue

        links = scanned_data[original_title]
        if isinstance(links, list):
            master = links[0]
            parts = "\n".join([f"• [Part {i+1}]({url})" for i, url in enumerate(links)])
            response.append(f"🎬 **{original_title.title()}**\n🔗 **Master Link:** [Watch Now]({master})\n📦 **Parts:**\n{parts}")
        else:
            response.append(f"🎬 **{original_title.title()}**\n🔗 [Click to Download]({links})")

    if response:
        bot.reply_to(message, "Here’s what I found for you, babe 🥵\n\n" + "\n\n".join(response), parse_mode="Markdown")
    else:
        bot.reply_to(message, "Couldn’t find that 😢 Maybe it’s not uploaded yet or your spelling's off.")

# Handle new uploads
@bot.message_handler(content_types=["document", "video"])
def store_files(message):
    file_name = message.document.file_name if message.document else message.video.file_name
    link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
    title = clean_title(os.path.splitext(file_name)[0])
    now = datetime.now()

    if title in scanned_data:
        if isinstance(scanned_data[title], list):
            if link not in scanned_data[title]:
                scanned_data[title].append(link)
        else:
            scanned_data[title] = [scanned_data[title], link]
    else:
        scanned_data[title] = [link]
    timestamp_data[title] = now

    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)
    with open("timestamp_data.pkl", "wb") as f:
        pickle.dump(timestamp_data, f)

# Start bot
print("💋 Sydney Sweeney bot is now running...")
bot.polling()
