import os
import sqlite3
import json
from pathlib import Path
from typing import Optional


def get_default_db_path() -> str:
    """Return default database file path from environment or project data directory."""
    env_path = os.getenv("DATABASE_PATH")
    if env_path:
        return env_path
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "knowledge_brain.db")


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open and return a connection to the SQLite database with WAL mode and row factory."""
    path = db_path or get_default_db_path()
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for concurrent reads and writes when not in-memory
    if path != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables and full-text search indexes."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Core articles table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                canonical_url TEXT NOT NULL,
                title TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                clean_text TEXT NOT NULL,
                last_modified TEXT,
                ingested_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            );
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_canonical ON articles(canonical_url);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);")

        # FTS5 full-text search virtual table for BM25 keyword retrieval
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                title,
                clean_text,
                url UNINDEXED,
                canonical_url UNINDEXED
            );
            """
        )

        # Ingestion run tracking and checkpoints
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                pages_discovered INTEGER DEFAULT 0,
                pages_processed INTEGER DEFAULT 0,
                pages_new INTEGER DEFAULT 0,
                pages_changed INTEGER DEFAULT 0,
                pages_unchanged INTEGER DEFAULT 0,
                pages_removed INTEGER DEFAULT 0,
                errors TEXT DEFAULT '[]',
                checkpoint_url TEXT
            );
            """
        )

        # Escalations table for unanswered questions
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                reason TEXT NOT NULL,
                context TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                expert_answer TEXT,
                resolved_by TEXT,
                created_at TEXT NOT NULL,
                resolved_at TEXT
            );
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_escalations_status ON escalations(status);")

        conn.commit()
