import os
import pickle
import re
from datetime import datetime, timedelta
from telebot import TeleBot, types

# Initialize the bot with your token
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)

# Load existing data or initialize empty dictionaries
if os.path.exists("scanned_data.pkl"):
    with open("scanned_data.pkl", "rb") as f:
        scanned_data = pickle.load(f)
else:
    scanned_data = {}

if os.path.exists("timestamps.pkl"):
    with open("timestamps.pkl", "rb") as f:
        timestamps = pickle.load(f)
else:
    timestamps = {}

def clean_title(name):
    """
    Cleans the file name to extract a base title for grouping.
    """
    name = name.lower()
    name = re.sub(r'\b(720p|1080p|480p|4k|x264|x265|bluray|webrip|web-dl|hdrip|dvdrip|hevc|h264|h265|multi|dubbed|uncut|ddp5\.1|dd5\.1|esub|eng|hin|dual audio)\b', '', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip()

@bot.message_handler(content_types=["document", "video"])
def handle_file_upload(message):
    """
    Handles the uploading of files, groups them, and generates master links.
    """
    file_name = message.document.file_name if message.document else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
    base_title = clean_title(os.path.splitext(file_name)[0])
    now = datetime.now()

    # Update scanned_data
    if base_title in scanned_data:
        if file_link not in scanned_data[base_title]:
            scanned_data[base_title].append(file_link)
    else:
        scanned_data[base_title] = [file_link]

    # Update timestamps
    timestamps[base_title] = now

    # Save updated data
    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)
    with open("timestamps.pkl", "wb") as f:
        pickle.dump(timestamps, f)

    # Generate master link message
    links = scanned_data[base_title]
    message_text = f"🎬 *{base_title.title()}*\n\n"
    for idx, link in enumerate(links, 1):
        message_text += f"▶️ [Part {idx}]({link})\n"

    sent_message = bot.send_message(message.chat.id, message_text, parse_mode="Markdown")
    master_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{sent_message.message_id}"
    bot.reply_to(message, f"Master Link: {master_link}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """
    Handles text messages and provides master links if available.
    """
    query = clean_title(message.text)
    if query in scanned_data:
        links = scanned_data[query]
        message_text = f"🎬 *{query.title()}*\n\n"
        for idx, link in enumerate(links, 1):
            message_text += f"▶️ [Part {idx}]({link})\n"
        bot.reply_to(message, message_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "Sorry, I couldn't find any matching files.")

def cleanup_old_entries():
    """
    Removes entries older than 1 day from scanned_data and timestamps.
    """
    now = datetime.now()
    keys_to_delete = [key for key, timestamp in timestamps.items() if now - timestamp > timedelta(days=1)]
    for key in keys_to_delete:
        scanned_data.pop(key, None)
        timestamps.pop(key, None)
    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)
    with open("timestamps.pkl", "wb") as f:
        pickle.dump(timestamps, f)

# Start the bot
bot.polling()
