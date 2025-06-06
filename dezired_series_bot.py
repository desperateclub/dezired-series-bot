import os
import pickle
import re
import random
from fuzzywuzzy import process
import telebot
from telebot import types

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it in your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)

# Load scanned data
scanned_data = {}
if os.path.exists("scanned_data.pkl"):
    with open("scanned_data.pkl", "rb") as f:
        try:
            scanned_data = pickle.load(f)
        except EOFError:
            scanned_data = {}

# Title cleaner to normalize movie/series names
def clean_title(title):
    title = re.sub(r'\.(\d{3,4}p|BluRay|WEBRip|x264|XviD|HDRip|HEVC|AAC|MP3|DDP|EVO|RARBG|YIFY|AMZN|NF|HD|SD)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'[^a-zA-Z0-9\s]', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title.lower()

# Save function to update scanned_data.pkl
def save_data():
    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)

# Handle new document/video uploads
def handle_new_file(message):
    file_name = message.document.file_name if message.document else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"

    base_name = clean_title(os.path.splitext(file_name)[0])

    if base_name in scanned_data:
        if isinstance(scanned_data[base_name], list):
            scanned_data[base_name].append(file_link)
        else:
            scanned_data[base_name] = [scanned_data[base_name], file_link]
    else:
        scanned_data[base_name] = file_link

    save_data()

@bot.message_handler(content_types=["document", "video"])
def on_file_upload(message):
    handle_new_file(message)

# Intelligent and sassy responses
@bot.message_handler(func=lambda m: True, content_types=["text"])
def on_text(message):
    text = message.text.strip().lower()

    greetings = ["hi", "hello", "hey", "who are you"]
    flirts = ["i love you", "marry me", "are you single"]

    if any(greet in text for greet in greetings):
        bot.reply_to(message, "Hey there! Sydney Sweeney here, your one-stop entertainment goddess 💁‍♀️")
        return

    if any(flirt in text for flirt in flirts):
        bot.reply_to(message, "Aww, you’re cute 😘 but I only date people who binge-watch like a pro.")
        return

    if text in ["suggest a movie", "movie please", "suggest movie"]:
        movies = [k for k in scanned_data if 's01' not in k and 'season' not in k]
        if movies:
            choice = random.choice(movies)
            result = scanned_data[choice]
            send_result(message, choice, result)
        else:
            bot.reply_to(message, "😬 No movies in my stash right now. Ask the admins maybe?")
        return

    if text in ["suggest a series", "series please", "suggest series"]:
        series = [k for k in scanned_data if 's01' in k or 'season' in k]
        if series:
            choice = random.choice(series)
            result = scanned_data[choice]
            send_result(message, choice, result)
        else:
            bot.reply_to(message, "😬 I don’t see any series yet. Ask the admins to drop some episodes!")
        return

    # Try to match with year
    year_match = re.search(r'(\d{4})', text)
    search_title = clean_title(text)

    candidates = list(scanned_data.keys())
    best_match, score = process.extractOne(search_title, candidates)

    if score >= 65:
        result = scanned_data[best_match]
        send_result(message, best_match, result)
    else:
        suggestions = [t.title() for t, s in process.extract(search_title, candidates, limit=3) if s > 50]
        suggestion_msg = "\nDid you mean: " + ", ".join(suggestions) if suggestions else ""
        bot.reply_to(message, f"😕 Couldn't find that. Maybe it's not uploaded yet.{suggestion_msg}")

# Helper to send results

def send_result(message, title, result):
    if isinstance(result, list):
        reply_text = f"🎬 *{title.title()}* has multiple files:\n\n"
        reply_text += "\n".join([f"🔗 [Part {i + 1}]({link})" for i, link in enumerate(result)])
    else:
        reply_text = f"🎬 *{title.title()}*:\n🔗 [Click to Download]({result})"

    bot.reply_to(message, reply_text, parse_mode="Markdown")

print("Sydney Sweeney is live and sassier than ever 💅")
bot.polling()
