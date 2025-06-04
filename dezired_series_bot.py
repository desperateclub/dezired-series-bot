import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = '8044842702:AAGOJ3AXzQ-CpUnVaCABFJ-3LXy-mCiRFVg'
GROUP_CHAT_ID = -1001612892172  # Your group's chat ID

file_db = {}  # In-memory storage

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hey {update.effective_user.first_name}! I’m your Dezired Series Bot 🎬\nType a movie name to search.")

# Collect uploaded documents
async def file_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.chat.id != GROUP_CHAT_ID:
        return

    if message.document:
        caption = (message.caption or message.document.file_name or '').lower()
        link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
        file_db[caption] = link
        print(f"📥 Stored: {caption} → {link}")

# Search by user text
async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.chat.id != GROUP_CHAT_ID:
        return

    query = message.text.lower().strip().replace(" ", "").replace(".", "")
    results = []

    for title, link in file_db.items():
        normalized = title.replace(" ", "").replace(".", "")
        if query in normalized:
            results.append(link)

    if results:
        await message.reply_text(f"🎬 Found {len(results)} result(s):")
        for link in set(results):
            await message.reply_text(link)
    else:
        await message.reply_text(f"❌ Not found, {update.effective_user.first_name}! 😓")

# Scan group history
async def scan_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.chat.id != GROUP_CHAT_ID:
        return

    await message.reply_text("🔍 Scanning recent messages for documents...")
    count = 0

    async for msg in context.bot.get_chat(GROUP_CHAT_ID).iter_history(limit=1000):  # You can adjust limit
        if msg.document:
            caption = (msg.caption or msg.document.file_name or '').lower()
            link = f"https://t.me/c/{str(GROUP_CHAT_ID)[4:]}/{msg.message_id}"
            file_db[caption] = link
            count += 1

    await message.reply_text(f"✅ Scan complete! {count} files indexed.")

# Main runner
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan_history", scan_history))
    app.add_handler(MessageHandler(filters.Document.ALL, file_collector))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_movie))

    print("🎬 DeziredSeriesBot is running...")
    app.run_polling()

if __name__ == '__main__':
    run_bot()
