import telebot
from telebot.util import escape_markdown
import pickle
import os

TOKEN = "YOUR_BOT_TOKEN"
bot = telebot.TeleBot(TOKEN)

scanned_data = {}

DATA_FILE = "scanned_data.pkl"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "rb") as f:
        scanned_data = pickle.load(f)

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "✅ Dezired Series Bot is online and working!")

@bot.message_handler(commands=["scan_history"])
def scan_history(m):
    chat_id = m.chat.id
    scanned_data[chat_id] = {}
    limit = 1000  # number of past messages to scan

    for msg in bot.get_chat_history(chat_id, limit=limit):
        if msg.content_type == "document" and msg.document.file_name:
            filename = msg.document.file_name
            scanned_data[chat_id][filename.lower()] = msg

    with open(DATA_FILE, "wb") as f:
        pickle.dump(scanned_data, f)

    bot.reply_to(m, f"✅ Scanned last {limit} messages for documents!")

@bot.message_handler(func=lambda msg: True)
def search(m):
    q = m.text.strip()
    
    if not q or all(c in '.,' for c in q):
        return  # skip inputs like ".", ",", etc.

    chat_id = m.chat.id

    if chat_id not in scanned_data:
        bot.reply_to(m, "⚠️ No data found. Please use /scan_history first.")
        return

    results = []
    for filename, msg in scanned_data[chat_id].items():
        if q.lower() in filename:
            link = f"https://t.me/c/{str(chat_id)[4:]}/{msg.message_id}"
            results.append(f"📂 [{filename}]({link})")

    if results:
        bot.reply_to(m, "\n\n".join(results), parse_mode="Markdown", disable_web_page_preview=True)
    else:
        from telebot.util import escape_markdown
        safe_q = escape_markdown(q)
        bot.reply_to(m, f"❌ *{safe_q}* not found. Try /scan_history first!", parse_mode="Markdown")

bot.infinity_polling()
