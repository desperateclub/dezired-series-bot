import os
import pickle
import random
import telebot
from fuzzywuzzy import process

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

# Load or initialize scanned data safely
scanned_data = {}

if os.path.exists("scanned_data.pkl"):
    try:
        with open("scanned_data.pkl", "rb") as f:
            scanned_data = pickle.load(f)
    except EOFError:
        scanned_data = {}

# Save function to update scanned_data.pkl
def save_data():
    with open("scanned_data.pkl", "wb") as f:
        pickle.dump(scanned_data, f)

# Watch for new document/video uploads
@bot.message_handler(content_types=["document", "video"])
def handle_new_file(message):
    try:
        file_name = message.document.file_name if message.document else message.video.file_name
        file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"

        base_name = os.path.splitext(file_name)[0].strip().lower()

        if base_name in scanned_data:
            if isinstance(scanned_data[base_name], list):
                scanned_data[base_name].append(file_link)
            else:
                scanned_data[base_name] = [scanned_data[base_name], file_link]
        else:
            scanned_data[base_name] = file_link

        save_data()
    except Exception as e:
        print(f"Error while saving file: {e}")

# Handle all messages as natural language
@bot.message_handler(func=lambda message: True, content_types=["text"])
def handle_text(message):
    query = message.text.strip().lower()

    if not query:
        return

    # Suggestion trigger
    if "random" in query or "suggest" in query or "any good" in query:
        if not scanned_data:
            bot.reply_to(message, "📭 No movies in the vault yet.")
            return

        random_title = random.choice(list(scanned_data.keys()))
        result = scanned_data[random_title]

        if isinstance(result, list):
            reply_text = f"🎲 Random Pick: **{random_title.title()}** has multiple parts:\n\n"
            reply_text += "\n".join([f"🔗 [Part {i + 1}]({link})" for i, link in enumerate(result)])
        else:
            reply_text = f"🎲 Random Pick: **{random_title.title()}**:\n🔗 [Click to Download]({result})"

        bot.reply_to(message, reply_text, parse_mode="Markdown")
        return

    # Match movie name using fuzzy logic
    if scanned_data:
        best_match, score = process.extractOne(query, scanned_data.keys())
        if score >= 70:
            result = scanned_data[best_match]
            if isinstance(result, list):
                reply_text = f"🎬 **{best_match.title()}** has multiple parts/files:\n\n"
                reply_text += "\n".join([f"🔗 [Part {i + 1}]({link})" for i, link in enumerate(result)])
            else:
                reply_text = f"🎬 **{best_match.title()}**:\n🔗 [Click to Download]({result})"

            bot.reply_to(message, reply_text, parse_mode="Markdown")
            return

    # If nothing found
    bot.reply_to(message, "🤷 Couldn't find it! Ask the admins, they might drop it soon if available.")

# Start polling
print("🎬 Sydney Sweeney Bot is now live!")
bot.polling()
