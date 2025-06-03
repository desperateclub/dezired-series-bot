import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === Your Bot Token & Group Chat ID ===
BOT_TOKEN = '8044842702:AAGOJ3AXzQ-CpUnVaCABFJ-3LXy-mCiRFVg'
GROUP_CHAT_ID = -1001612892172

# === In-memory database ===
# We'll store movie keys normalized to a list of links (for multiple parts)
file_db = {}

# === Logging ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def normalize_text(text: str) -> str:
    """Normalize text by removing non-alphanumeric characters and lowercasing."""
    return re.sub(r'[^a-z0-9]', '', text.lower())

# === Start command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Hey {update.effective_user.first_name}! I'm your Dezired Series Bot 🍿\nSend a movie name to search!"
    )

# === Collect files (document-only for now) ===
async def file_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.chat.id != GROUP_CHAT_ID:
        return

    if message.document:
        # Use caption if present, else fallback to filename
        raw_title = (message.caption or message.document.file_name or '').strip()
        if not raw_title:
            return
        key = normalize_text(raw_title)
        link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"

        if key in file_db:
            if link not in file_db[key]:
                file_db[key].append(link)
        else:
            file_db[key] = [link]
        print(f"📥 Stored: {raw_title} (key: {key}) → {link}")

# === Search ===
async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.chat.id != GROUP_CHAT_ID:
        return

    user_name = update.effective_user.first_name or "there"
    query = normalize_text(message.text.strip())
    if not query:
        await message.reply_text(f"❌ Please enter a valid movie name, {user_name}!")
        return

    # Find matching keys by partial substring match
    matched_keys = [key for key in file_db if query in key]

    if matched_keys:
        # For now send only the first matched key with all links combined as "master"
        master_key = matched_keys[0]
        links = file_db[master_key]
        response = f"🎬 Hey {user_name}, found these links for your movie:\n" + "\n".join(links)
        await message.reply_text(response)
    else:
        await message.reply_text(f"❌ Not available, {user_name}! 😓")

# === Main ===
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, file_collector))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_movie))

    print("🎬 DeziredSeriesBot is running...")
    app.run_polling()

# === Start Bot ===
if __name__ == '__main__':
    run_bot()
