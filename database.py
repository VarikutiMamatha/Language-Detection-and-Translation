"""
database.py
SQLite storage for translation history.
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "data/translations.db"


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                detected_lang TEXT,
                detected_confidence REAL,
                target_lang TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                backend TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_translation(original_text, detected_lang, detected_confidence,
                      target_lang, translated_text, backend):
    with _connect() as conn:
        conn.execute(
            """INSERT INTO translations
               (original_text, detected_lang, detected_confidence, target_lang,
                translated_text, backend, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (original_text, detected_lang, detected_confidence, target_lang,
             translated_text, backend, datetime.utcnow().isoformat()),
        )
        conn.commit()


def get_history(limit: int = 50):
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM translations ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def clear_history():
    with _connect() as conn:
        conn.execute("DELETE FROM translations")
        conn.commit()
