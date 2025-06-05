import os
import pickle
import telebot
from fuzzywuzzy import process
import tempfile
import shutil

# Load environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

# Ensure BOT_TOKEN is present
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it in your environment variables.")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Safe loading of scanned_data.pkl
scanned_data = {}
if os.path.exists("scanned_data.pkl"):
    try:
        with open("scanned_data.pkl", "rb") as f:
            scanned_data = pickle.load(f)
    except (EOFError, pickle.UnpicklingError):
        print("⚠️ scanned_data.pkl was empty or corrupted. Starting fresh.")
        scanned_data = {}

# Safe saving with atomic write
def save_data():
    with tempfile.NamedTemporaryFile('wb', delete=False, dir='.') as tf:
        pickle.dump(scanned_data, tf)
        tempname = tf.name
    shutil.move(tempname, "scanned_data.pkl")

# Handle incoming files
@bot.message_handler(content_types=["document", "video"])
def handle_new_file(message):
    file_name = message.document.file_name if message.document else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"

    base_name = os.path.splitext(file_name)[0].strip().lower()

    # Prioritize grouping by matching name
    if base_name in scanned_data:
        if isinstance(scanned_data[base_name], list):
            scanned_data[base_name].append(file_link)
        else:
            scanned_data[base_name] = [scanned_data[base_name], file_link]
    else:
        scanned_data[base_name] = file_link

    save_data()

# Start command
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "🎬 Hey there! I’m Sydney Sweeney, the movie matchmaker of *Dezired Series*! Just drop a movie name and I’ll do my thing 😉")

# Search for movie
@bot.message_handler(func=lambda message: True, content_types=["text"])
def search_movie(message):
    query = message.text.strip().lower()

    if not scanned_data:
        bot.reply_to(message, "⚠️ Nothing in the collection yet!")
        return

    best_match, score = process.extractOne(query, scanned_data.keys())

    if score >= 70:
        result = scanned_data[best_match]
        if isinstance(result, list):
            reply_text = f"🎬 **{best_match.title()}** has multiple parts:\n\n"
            reply_text += "\n".join([f"🔗 [Part {i+1}]({link})" for i, link in enumerate(result)])
        else:
            reply_text = f"🎬 **{best_match.title()}**:\n🔗 [Click to Download]({result})"
        bot.reply_to(message, reply_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Couldn't find it! Maybe ask the admins to fetch it for you.")

# Run bot
bot.polling()
