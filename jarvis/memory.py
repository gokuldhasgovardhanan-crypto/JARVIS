import sqlite3
from pathlib import Path

DATA_DIR = Path.home() / "AppData" / "Local" / "PersonalJarvis"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "jarvis_memory.db"


class MemoryStore:
    def __init__(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS notes "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, note TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )

    def save_note(self, note: str):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO notes (note) VALUES (?)", (note,))

    def get_notes(self):
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                "SELECT note FROM notes ORDER BY id DESC LIMIT 20"
            ).fetchall()
        return [row[0] for row in rows]
