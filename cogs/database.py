"""Database utility functions for cogs"""
import json
import os
from datetime import datetime

def load_db(filename="database.json"):
    """
    Loads the JSON database from disk, returns an empty dict if it doesn't exist.
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}
    except FileNotFoundError:
        with open(filename, 'w') as f:
            return {}

def save_db(data, filename="database.json"):
    """
    Saves the provided dict to the JSON database with indentation for readability.
    """
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def save_message(guild_id, user_id, message):
    """
    Appends a message dict to the conversation history for (guild_id, user_id).
    """
    db = load_db()
    
    key = f"{guild_id}_{user_id}"
    if key not in db:
        db[key] = {"messages": []}
    
    # Add message with timestamp
    db[key]["messages"].append({
        "content": message,
        "timestamp": str(datetime.now())
    })
    
    save_db(db)