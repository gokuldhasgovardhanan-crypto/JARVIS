import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from jarvis.utils.logging_config import logger


class DatabaseManager:
    """Manages SQLite database connections and schema migrations for JARVIS."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides a transactional database connection context."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.error(f"Database transaction error: {exc}", exc_info=True)
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initializes tables and indexes with WAL mode enabled."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("PRAGMA foreign_keys=ON;")

                # Notes table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        note TEXT NOT NULL,
                        tags TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

                # Conversations history table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        detected_language TEXT DEFAULT 'en',
                        response_language TEXT DEFAULT 'en',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

                # Settings and Preferences table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

                # Windows Automation Audit Log
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action_type TEXT NOT NULL,
                        target TEXT NOT NULL,
                        status TEXT NOT NULL,
                        details TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

                # Create useful indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);")
                conn.commit()
                logger.info(f"Initialized JARVIS SQLite database at {self.db_path}")
        except Exception as exc:
            logger.error(f"Failed to initialize database: {exc}", exc_info=True)
            raise
