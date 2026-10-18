from typing import List, Dict, Any, Optional
from jarvis.memory.database import DatabaseManager
from jarvis.config import config
from jarvis.utils.logging_config import logger


class MemoryRepository:
    """Repository layer for persisting and retrieving notes, conversation history, and settings."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager(config.db_path)

    # --- Notes CRUD ---
    def save_note(self, note: str, tags: str = "") -> int:
        """Saves a new note to the database. Returns note ID."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (note, tags) VALUES (?, ?)", (note.strip(), tags.strip())
            )
            note_id = cursor.lastrowid
            logger.info(f"Saved note with ID: {note_id}")
            return note_id

    def get_notes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent notes."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, note, tags, created_at, updated_at FROM notes ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """Searches notes by keyword."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, note, tags, created_at FROM notes WHERE note LIKE ? ORDER BY id DESC",
                (f"%{query}%",),
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_note(self, note_id: int) -> bool:
        """Deletes a note by its ID."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            return cursor.rowcount > 0

    def clear_all_notes(self) -> int:
        """Clears all stored notes."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM notes")
            return cursor.rowcount

    # --- Conversation History ---
    def add_conversation_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        detected_language: str = "en",
        response_language: str = "en",
    ) -> int:
        """Persists a conversation exchange turn."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO conversations 
                (session_id, role, content, detected_language, response_language) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, role, content, detected_language, response_language),
            )
            return cursor.lastrowid

    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetches the conversation messages for the current session."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT role, content, detected_language, response_language, created_at 
                FROM conversations 
                WHERE session_id = ? 
                ORDER BY id ASC LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def clear_conversation_history(self, session_id: Optional[str] = None) -> int:
        """Clears conversation messages for a session or globally."""
        with self.db.get_connection() as conn:
            if session_id:
                cursor = conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            else:
                cursor = conn.execute("DELETE FROM conversations")
            return cursor.rowcount

    # --- Settings & Preferences ---
    def set_setting(self, key: str, value: str) -> None:
        """Sets or updates a configuration setting in SQLite."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, value),
            )

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Gets a stored setting or returns default."""
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    # --- Windows Automation Audit Log ---
    def log_action(self, action_type: str, target: str, status: str, details: str = "") -> int:
        """Audits an executed or rejected action safely."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_logs (action_type, target, status, details) 
                VALUES (?, ?, ?, ?)
                """,
                (action_type, target, status, details),
            )
            return cursor.lastrowid

    def get_recent_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent action audit log entries."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, action_type, target, status, details, created_at FROM audit_logs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
