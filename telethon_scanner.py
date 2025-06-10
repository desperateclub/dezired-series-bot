import os, json, time
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
GROUP_ID = int(os.getenv("GROUP_ID"))
DATA_FILE = "scanned_data.json"

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def scan_history():
    data = {}
    with client:
        for msg in client.iter_messages(GROUP_ID, limit=None):
            if msg.document and msg.document.file_name:
                key = msg.document.file_name.lower().rsplit('.', 1)[0]
                data[key] = {"file_name": msg.document.file_name, "message_id": msg.id}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Scanned {len(data)} files.")

if __name__ == "__main__":
    scan_history()
