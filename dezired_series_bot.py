import os
import pickle
import telebot
from telebot import types
from fuzzywuzzy import process

# Load environment variables correctly
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

# Ensure BOT_TOKEN is present
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing. Set it in your environment variables.")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Load or initialize scanned data
scanned_data = {}

if os.path.exists("scanned_data.pkl"):
    with open("scanned_data.pkl", "rb") as f:
        scanned_data = pickle.load(f)

# Save function to update scanned_data.pkl
def save_data():
    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)

# Detect new files sent to group and update scanned_data
@bot.message_handler(content_types=["document", "video"])
def handle_new_file(message):
    file_name = message.document.file_name if message.document else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"

    base_name = os.path.splitext(file_name)[0].strip().lower()

    # Add or update file entry
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
    bot.reply_to(message, "👋 Welcome to Dezired Series Bot!\n\nSend me a movie name and I’ll fetch the download link if it’s available.")

# Movie search
@bot.message_handler(func=lambda message: True, content_types=["text"])
def search_movie(message):
    query = message.text.strip().lower()

    if not scanned_data:
        bot.reply_to(message, "⚠️ No data available yet.")
        return

    best_match, score = process.extractOne(query, scanned_data.keys())

    if score >= 70:
        result = scanned_data[best_match]
        if isinstance(result, list):
            reply_text = f"🎬 **{best_match.title()}** has multiple parts/files:\n\n"
            reply_text += "\n".join([f"🔗 [Part {i + 1}]({link})" for i, link in enumerate(result)])
        else:
            reply_text = f"🎬 **{best_match.title()}**:\n🔗 [Click to Download]({result})"

        bot.reply_to(message, reply_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Movie not found. Please check the spelling or wait for admins to upload the file if available.")

# Start polling
bot.polling()
