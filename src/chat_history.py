import json
import os 
from datetime import datetime

CHAT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "chat_history.json")

def save_conversations(conversations:dict):
    "save chats to json"
    try:
        with open(CHAT_HISTORY_FILE,"w", encoding="utf-8")as f:
             json.dump(conversations, f, indent=2, ensure_ascii=False)
    except Exception as e:
         print(f"Error saving chat history: {e}")

def load_conversations() -> dict:
    """Load conversations from disk. Returns empty dict if file doesn't exist."""
    if not os.path.exists(CHAT_HISTORY_FILE):
        return {}
    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading chat history: {e}")
        return {}
    
def delete_conversation(chat_id: str):
    """Delete a single conversation from disk."""
    conversations = load_conversations()
    if chat_id in conversations:
        del conversations[chat_id]
        save_conversations(conversations)