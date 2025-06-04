import logging
from telegram import Update, Document
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from collections import defaultdict
import re

# === BOT CREDENTIALS ===
BOT_TOKEN = "8044842702:AAGOJ3AXzQ-CpUnVaCABFJ-3LXy-mCiRFVg"
GROUP_CHAT_ID = -1001612892172

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === IN-MEMORY DB ===
movie_links = defaultdict(list)

# === HELPER FUNCTIONS ===
def clean_title(title: str) -> str:
    title = re.sub(r'\W+', ' ', title)
    return title.strip().lower()

def match_movie(query: str, title: str) -> bool:
    return clean_title(query) in clean_title(title)

def mention_user(update: Update) -> str:
    return update.effective_user.first_name if update.effective_user else "there"

# === HANDLERS ===
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.document:
        doc: Document = update.message.document
        title = doc.file_name or "Unnamed"
        link = f"https://t.me/c/{str(GROUP_CHAT_ID)[4:]}/{update.message.message_id}"
        movie_links[clean_title(title)].append(link)
        logger.info(f"Saved: {title} -> {link}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = mention_user(update)
    await update.message.reply_text(f"👋 Hello {name}! I'm DeziredSeriesBot. Just type a movie name and I'll find the link!")

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    name = mention_user(update)
    query = update.message.text.strip().lower()
    for title, links in movie_links.items():
        if match_movie(query, title):
            await update.message.reply_text(f"🎬 Hey {name}! Found this for *{title.title()}*:\n{links[0]}", parse_mode="Markdown")
            return
    await update.message.reply_text(f"😓 Sorry {name}, not available yet...")

async def scan_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_CHAT_ID:
        await update.message.reply_text("⚠️ This command only works in the main group.")
        return

    count = 0
    async for msg in context.bot.get_chat(GROUP_CHAT_ID).iter_history(limit=1000):
        if msg.document:
            title = msg.document.file_name or "Unnamed"
            link = f"https://t.me/c/{str(GROUP_CHAT_ID)[4:]}/{msg.message_id}"
            key = clean_title(title)
            if link not in movie_links[key]:
                movie_links[key].append(link)
                count += 1

    name = mention_user(update)
    await update.message.reply_text(f"✅ Done, {name}! Scanned and added {count} links from history.")

# === MAIN ===
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan_history", scan_history))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_movie))
    print("Starting DeziredSeriesBot...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()
