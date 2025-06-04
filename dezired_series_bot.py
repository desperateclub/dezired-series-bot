import telebot
import pickle
import os
import difflib
from collections import defaultdict

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN") or "your_bot_token_here"
PICKLE_FILE = 'scanned_data.pkl'

bot = telebot.TeleBot(BOT_TOKEN)

# === Load scanned data ===
if os.path.exists(PICKLE_FILE):
    with open(PICKLE_FILE, 'rb') as f:
        scanned_data = pickle.load(f)
else:
    scanned_data = {}
    print(f"{PICKLE_FILE} not found. Starting with empty database.")

# Convert scanned_data into defaultdict(list) format for easy grouping
movie_links = defaultdict(list)
for name, link in scanned_data.items():
    movie_links[name.lower()].append(link)

# === Save data ===
def save_data():
    flattened = {}
    for title, links in movie_links.items():
        for link in links:
            flattened[title] = link
    with open(PICKLE_FILE, 'wb') as f:
        pickle.dump(flattened, f)

# === Utility: Find best match for user query ===
def find_best_match(query):
    all_titles = list(movie_links.keys())
    matches = difflib.get_close_matches(query.lower(), all_titles, n=1, cutoff=0.4)
    return matches[0] if matches else None

# === Handle new documents added to group ===
@bot.message_handler(content_types=['document', 'video'])
def handle_new_file(message):
    if message.chat.type != 'supergroup' and message.chat.type != 'group':
        return

    file_name = message.document.file_name if message.document else message.video.file_name
    file_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"

    base_name = file_name.rsplit('.', 1)[0].lower().replace('_', ' ').replace('.', ' ').strip()
    movie_links[base_name].append(file_link)
    save_data()
    print(f"[NEW] Saved: {base_name} -> {file_link}")

# === Handle user queries ===
@bot.message_handler(func=lambda message: True)
def handle_query(message):
    query = message.text.strip().lower()
    match = find_best_match(query)

    if match:
        links = movie_links[match]
        reply = f"🎬 *{match.title()}* - {len(links)} file(s) found:\n"
        if len(links) > 1:
            reply += f"[📂 View Files](https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id})\n"
            for i, link in enumerate(links[:3], 1):  # Preview max 3 links
                reply += f"{i}. [Link]({link})\n"
        else:
            reply += f"[🎥 Download Now]({links[0]})\n"
        bot.reply_to(message, reply, parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Sorry, I couldn't find anything for that. Please try again with a different name.")

# === Start polling ===
print("Bot is running...")
bot.infinity_polling()
