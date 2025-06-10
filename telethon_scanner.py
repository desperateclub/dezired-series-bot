from telethon.sync import TelegramClient
from telethon.tl.types import DocumentAttributeFilename
import os
import json

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_str = os.getenv("TELETHON_SESSION_STRING")
group_id = int(os.getenv("GROUP_ID"))

data_file = "scanned_data.json"

# Load existing data
try:
    with open(data_file, "r") as f:
        scanned_data = json.load(f)
except:
    scanned_data = {}

client = TelegramClient(StringSession(session_str), api_id, api_hash)

async def scan_history():
    async with client:
        async for message in client.iter_messages(group_id, limit=None):
            if message.document and message.file and message.file.name:
                title = message.file.name.rsplit(".", 1)[0].lower().strip()
                scanned_data[title] = {
                    "file_id": message.id,
                    "name": message.file.name
                }

        with open(data_file, "w") as f:
            json.dump(scanned_data, f, indent=2)
