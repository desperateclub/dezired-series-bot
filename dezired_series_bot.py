import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatAction

# === Your Bot Token & Group Chat ID ===
import os
BOT_TOKEN = os.getenv("8044842702:AAGOJ3AXzQ-CpUnVaCABFJ-3LXy-mCiRFVg")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "-1001612892172"))

# === In-memory database ===
file_db = {}

# === Logging ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# === Start command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey there! I'm your Dezired Series Bot 🍿\nJust send a movie name to search!")

# === Collect files (document-only for now) ===
async def file_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.chat.id != GROUP_CHAT_ID:
        return

    if message.document:
        caption = (message.caption or message.document.file_name or '').lower()
        link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"
        if caption not in file_db:
            file_db[caption] = [link]
        else:
            file_db[caption].append(link)
        print(f"📥 Stored: {caption} → {link}")

# === Search command ===
async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.chat.id != GROUP_CHAT_ID:
        return

    query = message.text.lower().strip()
    results = []

    for title, links in file_db.items():
        if query.replace(' ', '') in title.replace('.', '').replace(' ', ''):
            results.append((title, links))

    if results:
        for title, links in results:
            await message.reply_text(f"🎬 *{title}* → {links[0]}", parse_mode='Markdown')
    else:
        name = message.from_user.first_name
        await message.reply_text(f"❌ Not available, {name}! 😓")

# === Scan history command ===
async def scan_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GROUP_CHAT_ID:
        return

    await update.message.reply_text("🔍 Scanning group history... Please wait!")
    await context.bot.send_chat_action(chat_id=GROUP_CHAT_ID, action=ChatAction.TYPING)

    count = 0
    async for msg in context.bot.get_chat(GROUP_CHAT_ID).iter_history(limit=1000):
        if msg.document:
            caption = (msg.caption or msg.document.file_name or '').lower()
            link = f"https://t.me/c/{str(msg.chat.id)[4:]}/{msg.message_id}"
            if caption not in file_db:
                file_db[caption] = [link]
                count += 1

    await update.message.reply_text(f"✅ History scan complete. Added {count} new file(s)!")

# === Main ===
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan_history", scan_history))
    app.add_handler(MessageHandler(filters.Document.ALL, file_collector))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_movie))

    print("🎬 DeziredSeriesBot is running...")
    app.run_polling()

# === Start Bot ===
if __name__ == "__main__":
    run_bot()
