import pickle
import os
from fuzzywuzzy import process
import telebot

# Load environment variables
API_ID = os.getenv("21000508")
API_HASH = os.getenv("3669ffa5d2e6f6cdedfc3e6591a1ea2e")
BOT_TOKEN = os.getenv("8044842702:AAGOJ3AXzQ-CpUnVaCABFJ-3LXy-mCiRFVg")
GROUP_ID = os.getenv("-1001612892172")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Load scanned data
with open('scanned_data.pkl', 'rb') as f:
    scanned_data = pickle.load(f)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Send me a movie name, and I'll fetch the link if it's available.")

@bot.message_handler(func=lambda message: True)
def search_movie(message):
    query = message.text.strip()
    if not query:
        return

    best_match, score = process.extractOne(query, scanned_data.keys())

    if score >= 70:
        result = scanned_data[best_match]
        if isinstance(result, list):
            reply_text = f"🎬 **{best_match}** has multiple parts/files:\n\n"
            reply_text += "\n".join([f"🔗 [Part {i+1}]({link})" for i, link in enumerate(result)])
        else:
            reply_text = f"🎬 **{best_match}**:\n🔗 [Click to Download]({result})"

        bot.reply_to(message, reply_text, parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Couldn't find the movie. Try again with a different name or spelling.")

# Start polling
bot.polling()
