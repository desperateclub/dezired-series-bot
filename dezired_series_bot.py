import os
import telebot
from telebot import types
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))  # Telegram group ID where the bot is scanning

bot = telebot.TeleBot(BOT_TOKEN)
scanned_data = {}

# Avoid replies to ".", "..", etc.
IGNORED_QUERIES = {".", "..", "...", ",", "?", "-"}

def normalize(text):
    return ''.join(e.lower() for e in text if e.isalnum())

def clean_old_entries():
    now = datetime.now().timestamp()
    for title in list(scanned_data):
        filtered = [f for f in scanned_data[title] if now - f["timestamp"] < 86400]
        if filtered:
            scanned_data[title] = filtered
        else:
            del scanned_data[title]

@bot.message_handler(content_types=['document'])
def handle_new_files(message):
    if message.chat.id != GROUP_ID:
        return

    if not message.document:
        return

    file_name = message.document.file_name
    file_id = message.document.file_id
    user_name = message.from_user.first_name
    now = datetime.now().timestamp()

    normalized_title = normalize(file_name.split('.')[0])

    if normalized_title not in scanned_data:
        scanned_data[normalized_title] = []

    scanned_data[normalized_title].append({
        "file_id": file_id,
        "file_name": file_name,
        "user": user_name,
        "timestamp": now
    })

    print(f"[+] Added: {file_name} from {user_name}")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    if message.chat.id != GROUP_ID:
        return

    query = message.text.strip()
    if query in IGNORED_QUERIES:
        return

    clean_old_entries()

    normalized_query = normalize(query)
    matches = [
        (title, files)
        for title, files in scanned_data.items()
        if normalized_query in title
    ]

    if matches:
        response = f"🎬 <b>Results for:</b> <code>{query}</code>\n\n"
        for title, files in matches[:3]:
            latest = sorted(files, key=lambda x: x['timestamp'], reverse=True)[0]
            response += f"🎥 <b>{latest['file_name']}</b>\nUploaded by: {latest['user']}\n\n"
            bot.send_document(message.chat.id, latest['file_id'])
        bot.send_message(message.chat.id, response, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, f"😔 Couldn't find anything matching <code>{query}</code>", parse_mode='HTML')

print("🔥 Sydney Sweeney is online and serving sass 🎬")
bot.polling(non_stop=True)
