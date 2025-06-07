import os
import pickle
import time
import random
import re
from collections import defaultdict
from datetime import datetime, timezone

import telebot
from telebot.types import Message

API_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1001234567890"))
DATA_FILE = "scanned_data.pkl"

bot = telebot.TeleBot(API_TOKEN)
scanned_data = defaultdict(list)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "rb") as f:
        scanned_data = pickle.load(f)

symbol_only_pattern = re.compile(r"^[.,\\-\\s]*$")

emoji_map = {
    "romance": "😍",
    "action": "🔥",
    "comedy": "😂",
    "horror": "👻",
    "sci-fi": "🤖",
    "thriller": "😱",
    "anime": "🌸",
    "drama": "🎭"
}

fun_facts = [
    "🎬 Did you know? The first feature film ever made was 'The Story of the Kelly Gang' in 1906.",
    "🍿 Popcorn became popular in theaters during the Great Depression because it was cheap.",
    "🎥 The longest movie ever made is over 85 hours long! It's called 'Logistics'.",
    "📽️ Alfred Hitchcock never won an Oscar for Best Director.",
    "🎞️ Spider-Man was the first film to make $100 million in a single weekend."
]

def save_data():
    with open(DATA_FILE, "wb") as f:
        pickle.dump(scanned_data, f)

def search_movie(query):
    query_lower = query.lower()
    master_result = {}
    part_links = []

    for title, files in scanned_data.items():
        if query_lower in title.lower():
            part_links = files
            master_result["title"] = title
            master_result["files"] = files
            break

    return master_result, part_links

def clean_old_entries():
    now = datetime.now(timezone.utc).timestamp()
    for title in list(scanned_data.keys()):
        filtered = [f for f in scanned_data[title] if now - f["timestamp"] < 86400]
        if filtered:
            scanned_data[title] = filtered
        else:
            del scanned_data[title]
    save_data()

@bot.message_handler(func=lambda msg: True, content_types=["text"])
def handle_message(message: Message):
    if message.chat.id != GROUP_ID:
        return

    query = message.text.strip()
    if symbol_only_pattern.match(query):
        return

    if query.lower() in ["hi", "hello", "hey"]:
        bot.reply_to(message, f"Hey {message.from_user.first_name}! 🍿 Ask me for any movie!")
        return

    clean_old_entries()
    result, parts = search_movie(query)
    if result:
        title = result["title"]
        reply = f"🎬 *{title}*\n\n"

        for category in emoji_map:
            if category in title.lower():
                reply += emoji_map[category] + "\n"
                break

        reply += "\nHere’s your download links:\n"
        for file in parts:
            reply += f"🔗 [{file['name']}]({file['link']})\n"

        reply += f"\n🧲 *Master Link:* Coming soon or use parts above!\n"
        reply += f"\n💡 {random.choice(fun_facts)}"

        bot.reply_to(message, reply, parse_mode="Markdown")
    else:
        suggestions = [
            title for title in scanned_data.keys()
            if query.lower()[:4] in title.lower()
        ][:3]

        suggestion_text = ""
        if suggestions:
            suggestion_text = "\n\n🔍 Did you mean:\n" + "\n".join(f"• {s}" for s in suggestions)

        bot.reply_to(message, f"❌ Couldn't find anything for *{query}*{suggestion_text}", parse_mode="Markdown")

@bot.message_handler(content_types=["document"])
def scan_document(message: Message):
    if message.chat.id != GROUP_ID:
        return

    file_name = message.document.file_name
    file_link = f"https://t.me/c/{str(GROUP_ID)[4:]}/{message.message_id}"
    now = datetime.now(timezone.utc).timestamp()

    matched = False
    for title in scanned_data:
        if title.lower() in file_name.lower():
            scanned_data[title].append({"name": file_name, "link": file_link, "timestamp": now})
            matched = True
            break

    if not matched:
        scanned_data[file_name] = [{"name": file_name, "link": file_link, "timestamp": now}]

    save_data()

print("🔥 Sydney Sweeney is online and serving sass 🎬")
bot.polling(non_stop=True)
