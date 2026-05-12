"""
storage/database.py
SQLite layer for raw article storage.
 
Schema
------
articles
  id          INTEGER PRIMARY KEY AUTOINCREMENT
  url         TEXT UNIQUE          -- deduplication key
  title       TEXT
  body        TEXT
  source      TEXT                 -- label from config
  topic       TEXT                 -- gnews topic or rss/scraped
  published_at TEXT               -- ISO-8601 string or empty
  collected_at TEXT               -- when we inserted this row
  is_processed INTEGER DEFAULT 0  -- 0=raw, 1=sent to phase 2
"""
 
import sqlite3
import os
import logging
from datetime import datetime, timezone
from contextlib import contextmanager
 
from Personalized_news_summarizer.config.settings import DB_PATH
 
logger = logging.getLogger(__name__)
 
 
def _db_path() -> str:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH
 
 
@contextmanager
def get_connection():
    """Yield an open SQLite connection, commit on clean exit."""
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
 
 
def init_db() -> None:
    """Create tables if they don't exist yet."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                url          TEXT    UNIQUE NOT NULL,
                title        TEXT    NOT NULL,
                body         TEXT    DEFAULT '',
                source       TEXT    DEFAULT '',
                topic        TEXT    DEFAULT '',
                published_at TEXT    DEFAULT '',
                collected_at TEXT    NOT NULL,
                is_processed INTEGER DEFAULT 0
            )
        """)
        # Index for dedup checks and phase-2 queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_url
            ON articles(url)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_is_processed
            ON articles(is_processed)
        """)
    logger.info("Database initialised at %s", DB_PATH)
 
 
def insert_article(
    url: str,
    title: str,
    body: str = "",
    source: str = "",
    topic: str = "",
    published_at: str = "",
) -> bool:
    """
    Insert one article. Returns True if inserted, False if duplicate.
    Uses INSERT OR IGNORE so the UNIQUE constraint on url silently
    skips duplicates — no extra SELECT needed.
    """
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO articles
                (url, title, body, source, topic, published_at, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (url, title, body, source, topic, published_at, now),
        )
        inserted = cursor.rowcount > 0
    return inserted
 
 
def fetch_unprocessed(limit: int = 100) -> list[dict]:
    """Return up to `limit` articles not yet sent to phase 2."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM articles
            WHERE is_processed = 0
            ORDER BY collected_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
 
 
def mark_processed(article_ids: list[int]) -> None:
    """Mark articles as processed (is_processed = 1)."""
    if not article_ids:
        return
    placeholders = ",".join("?" * len(article_ids))
    with get_connection() as conn:
        conn.execute(
            f"UPDATE articles SET is_processed = 1 WHERE id IN ({placeholders})",
            article_ids,
        )
 
 
def article_count() -> dict:
    """Return total and unprocessed counts — useful for health checks."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        unprocessed = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE is_processed = 0"
        ).fetchone()[0]
    return {"total": total, "unprocessed": unprocessed}