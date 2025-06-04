import logging
import re
from telegram import Update, Document
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
import os

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# 🧠 File storage
file_db = {}

# Replace this with your group chat ID
GROUP_CHAT_ID = -1001612892172  # replace with actual group ID

# 🔧 Normalize strings for fuzzy matching
def normalize(text):
    return re.sub(r"[\W_]+", "", text.lower())

# 🔍 Search handler
async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    query = normalize(message.text.strip())
    if not query:
        return

    results = [link for title, link in file_db.items() if query in normalize(title)]

    if results:
        await message.reply_text(f"🎬 Here's what I found:\n\n" + "\n".join(results))
    else:
        await message.reply_text("😢 No matching movie found!")

# 📂 Scan history for files
async def scan_group_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_CHAT_ID:
        await update.message.reply_text("⛔ This command only works in the group.")
        return

    user = update.effective_user
    if not user:
        return

    await update.message.reply_text("📂 Scanning group history for movie files...")

    offset_id = None
    count = 0

    while True:
        history = await context.bot.get_chat_history(chat_id=GROUP_CHAT_ID, limit=100, offset_id=offset_id)
        if not history:
            break

        for message in history:
            offset_id = message.message_id
            doc: Document = message.document
            if doc:
                caption = (message.caption or doc.file_name or "untitled").lower()
                link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
                file_db[caption] = link
                count += 1

        if len(history) < 100:
            break

    await update.message.reply_text(f"✅ Done! Indexed {count} files!")

# 🧠 Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Send a movie name to get its link.")

# 🚀 Main bot runner
def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not set in environment!")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan_group_history))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_query))

    print("🤖 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
