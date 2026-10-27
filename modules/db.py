"""
modules/db.py – SQLite setup and CRUD helpers.
"""
import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from config import DB_PATH, SAMPLE_DIR

logger = logging.getLogger(__name__)


def _conn() -> sqlite3.Connection:
    """Get a SQLite connection with row_factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            subject     TEXT NOT NULL,
            content     TEXT NOT NULL,
            word_count  INTEGER,
            source      TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS summaries (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id       INTEGER REFERENCES notes(id),
            summary       TEXT,
            key_points    TEXT,
            flashcards    TEXT,
            quiz          TEXT,
            summary_words INTEGER,
            style         TEXT DEFAULT 'concise',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS quiz_scores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id     INTEGER REFERENCES notes(id),
            subject     TEXT,
            score       INTEGER,
            total       INTEGER,
            taken_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def save_note(title: str, subject: str, content: str, source: str = "paste") -> int:
    """Insert a note and return its ID."""
    wc = len(content.split()) if content else 0
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO notes (title, subject, content, word_count, source) VALUES (?,?,?,?,?)",
        (title, subject, content, wc, source),
    )
    note_id = cur.lastrowid
    conn.commit()
    conn.close()
    return note_id


def get_notes() -> pd.DataFrame:
    """Return all notes as a DataFrame."""
    conn = _conn()
    df = pd.read_sql_query(
        "SELECT id, title, subject, word_count, source, created_at FROM notes ORDER BY created_at DESC",
        conn,
    )
    conn.close()
    return df


def get_note(note_id: int) -> Optional[dict]:
    """Return a single note as a dict, or None."""
    conn = _conn()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def save_summary(note_id: int, summary: str, key_points: list,
                 flashcards: list, quiz: list = None, style: str = "concise") -> None:
    """Save a generated summary."""
    summary_words = len(summary.split()) if summary else 0
    conn = _conn()
    conn.execute(
        """INSERT INTO summaries (note_id, summary, key_points, flashcards, quiz, summary_words, style)
           VALUES (?,?,?,?,?,?,?)""",
        (
            note_id,
            summary,
            json.dumps(key_points),
            json.dumps(flashcards),
            json.dumps(quiz) if quiz else "[]",
            summary_words,
            style,
        ),
    )
    conn.commit()
    conn.close()


def get_summary(note_id: int) -> Optional[dict]:
    """Return the latest summary for a note, or None."""
    conn = _conn()
    row = conn.execute(
        "SELECT * FROM summaries WHERE note_id = ? ORDER BY created_at DESC LIMIT 1",
        (note_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    d = dict(row)
    d["key_points"] = json.loads(d["key_points"]) if d["key_points"] else []
    d["flashcards"] = json.loads(d["flashcards"]) if d["flashcards"] else []
    d["quiz"] = json.loads(d["quiz"]) if d["quiz"] else []
    return d


def save_quiz_score(note_id: int, score: int, total: int, subject: str = "") -> None:
    """Save a quiz score."""
    conn = _conn()
    conn.execute(
        "INSERT INTO quiz_scores (note_id, subject, score, total) VALUES (?,?,?,?)",
        (note_id, subject, score, total),
    )
    conn.commit()
    conn.close()


def get_quiz_scores() -> pd.DataFrame:
    """Return all quiz scores as a DataFrame."""
    conn = _conn()
    df = pd.read_sql_query(
        """SELECT qs.*, n.title, n.subject as note_subject
           FROM quiz_scores qs
           LEFT JOIN notes n ON qs.note_id = n.id
           ORDER BY qs.taken_at DESC""",
        conn,
    )
    conn.close()
    return df


def get_all_summaries() -> pd.DataFrame:
    """Return all summaries joined with notes."""
    conn = _conn()
    df = pd.read_sql_query(
        """SELECT s.*, n.title, n.subject, n.word_count as note_words
           FROM summaries s
           JOIN notes n ON s.note_id = n.id
           ORDER BY s.created_at DESC""",
        conn,
    )
    conn.close()
    return df


def load_sample_data() -> int:
    """Load sample data files from sample_data/ directory. Returns count loaded."""
    import os
    from modules.extract import extract_text_from_path

    if not os.path.exists(SAMPLE_DIR):
        logger.warning("Sample data directory not found: %s", SAMPLE_DIR)
        return 0

    count = 0
    for fname in sorted(os.listdir(SAMPLE_DIR)):
        if not fname.endswith((".txt", ".pdf")):
            continue
        fpath = os.path.join(SAMPLE_DIR, fname)
        content = extract_text_from_path(fpath)
        if not content.strip():
            continue

        # Derive title and subject from filename
        name = os.path.splitext(fname)[0]
        parts = name.split("_", 1)
        subject = parts[0].upper() if parts else "General"
        title = parts[1].replace("_", " ").title() if len(parts) > 1 else name.replace("_", " ").title()

        # Check for duplicates
        conn = _conn()
        existing = conn.execute(
            "SELECT id FROM notes WHERE title = ? AND subject = ?",
            (title, subject)
        ).fetchone()
        conn.close()

        if existing:
            continue

        note_id = save_note(title, subject, content, source="sample")
        count += 1
        try:
            from modules.chat import index_note
            index_note(note_id, title, content)
        except Exception:
            pass

    # Also load sample quiz scores if available
    csv_path = os.path.join(SAMPLE_DIR, "sample_quiz_scores.csv")
    if os.path.exists(csv_path):
        _load_sample_scores(csv_path)

    return count


def _load_sample_scores(csv_path: str) -> None:
    """Load sample quiz scores from CSV."""
    try:
        df = pd.read_csv(csv_path)
        conn = _conn()
        # Check if we already have scores
        existing = conn.execute("SELECT COUNT(*) FROM quiz_scores").fetchone()[0]
        if existing > 0:
            conn.close()
            return
        for _, row in df.iterrows():
            conn.execute(
                "INSERT INTO quiz_scores (note_id, subject, score, total, taken_at) VALUES (?,?,?,?,?)",
                (row.get("note_id", 1), row.get("subject", "General"),
                 row.get("score", 3), row.get("total", 5),
                 row.get("taken_at", datetime.now().isoformat())),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Failed to load sample scores: %s", e)


def note_count() -> int:
    """Return total number of notes."""
    conn = _conn()
    count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    conn.close()
    return count
