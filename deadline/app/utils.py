import json
from pathlib import Path

FILE_PATH = Path("database.json")

def load_reminders():
    if FILE_PATH.exists():
        with FILE_PATH.open("r", encoding="utf-8") as file:
            try:
                return json.load(file) or {}
            except json.decoder.JSONDecodeError:
                return {}

    return {}

def save_reminders(reminders):
    with FILE_PATH.open("w", encoding="utf-8") as file:
        json.dump(reminders, file, ensure_ascii=False, indent=4)
