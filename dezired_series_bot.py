import os
import pickle
import random
import telebot
from telebot import types
from fuzzywuzzy import process

# Load environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it in your environment variables.")

bot = telebot.TeleBot(BOT_TOKEN)

scanned_data = {}

# Safe load scanned_data.pkl
if os.path.exists("scanned_data.pkl"):
    try:
        with open("scanned_data.pkl", "rb") as f:
            scanned_data = pickle.load(f)
    except EOFError:
        scanned_data = {}

# Save function
def save_data():
    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)

# File handler
@bot.message_handler(content_types=["document", "video"])
def handle_new_file(message):
    file_name = message.document.file_name if message.document else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"

    base_name = os.path.splitext(file_name)[0].strip().lower()

    if base_name in scanned_data:
        if isinstance(scanned_data[base_name], list):
            if file_link not in scanned_data[base_name]:
                scanned_data[base_name].append(file_link)
        else:
            scanned_data[base_name] = [scanned_data[base_name], file_link]
    else:
        scanned_data[base_name] = file_link

    save_data()
    bot.reply_to(message, random.choice([
        "Got it! Adding to my stash 📂",
        "Oooh new drop? Noted 💾",
        "Yup, I see the file. Storing it with love ❤️"
    ]))

# Start command
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, random.choice([
        "Heya! I’m Sydney Sweeney 🤖✨ Your movie-finding baddie in Dezired Series 🎬",
        "Hello there 👋 I'm Sydney! Serving up your fav flicks right from Dezired Series 💿",
        "Welcome! Need a movie? You know I gotchu 💁‍♀️"
    ]))

# Random movie command
@bot.message_handler(commands=["random"])
def random_movie(message):
    if not scanned_data:
        bot.reply_to(message, "Uh-oh... no files yet 😅")
        return

    title = random.choice(list(scanned_data.keys()))
    result = scanned_data[title]
    if isinstance(result, list):
        link = result[0]
    else:
        link = result

    bot.reply_to(message, f"🎲 Random Pick: *{title.title()}*\n🔗 [Click to Watch]({link})", parse_mode="Markdown")

# Movie search
@bot.message_handler(func=lambda message: True, content_types=["text"])
def search_movie(message):
    query = message.text.strip().lower()

    if not scanned_data:
        bot.reply_to(message, "I haven’t stored anything yet. Drop some files first 📁")
        return

    best_match, score = process.extractOne(query, scanned_data.keys())

    if score >= 70:
        result = scanned_data[best_match]
        if isinstance(result, list):
            reply_text = f"🎬 *{best_match.title()}* has multiple parts:\n\n"
            reply_text += "\n".join([f"🔗 [Part {i + 1}]({link})" for i, link in enumerate(result)])
        else:
            reply_text = f"🎬 *{best_match.title()}*:\n🔗 [Click to Download]({result})"
        bot.reply_to(message, reply_text, parse_mode="Markdown")
    else:
        # Try giving up to 3 close matches
        suggestions = process.extract(query, scanned_data.keys(), limit=3)
        suggestion_text = "\n".join([f"🔍 {s[0].title()}" for s in suggestions if s[1] >= 50])

        if suggestion_text:
            bot.reply_to(message, f"🤷‍♀️ Couldn’t find that. But maybe you meant:\n\n{suggestion_text}")
        else:
            bot.reply_to(message, random.choice([
                "No clue what that is 🤔 Maybe try again later.",
                "Hmm, nothing on that yet. Let the admins handle it 😎",
                "Didn't find it. Either it doesn’t exist or it’s hidden better than Thanos 🧤"
            ]))

bot.polling()
