"""
SQLite Database module for HealthSaathi Voice Agent.
"""

import logging
import os
import sqlite3

logger = logging.getLogger("healthsathi.database")

DB_PATH = os.environ.get(
    "HEALTHSATHI_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "healthsathi_memory.db"),
)


def get_db_connection() -> sqlite3.Connection:
    """Create and return a SQLite database connection with row factory."""
    db_abs_path = os.path.abspath(DB_PATH)
    os.makedirs(os.path.dirname(db_abs_path), exist_ok=True)
    conn = sqlite3.connect(db_abs_path)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrent read performance
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Initialize SQLite database schema."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memories (
                user_id            TEXT PRIMARY KEY,
                name               TEXT,
                age_band           TEXT,
                language_preference TEXT,
                ongoing_conditions TEXT,
                last_triage_outcome TEXT,
                last_interaction   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outbound_calls (
                call_id             TEXT PRIMARY KEY,
                phone_number        TEXT NOT NULL,
                scheduled_time      TEXT,
                timezone            TEXT,
                status              TEXT NOT NULL,
                room_name           TEXT,
                participant_id      TEXT,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

        logger.info(f"SQLite database ready at {os.path.abspath(DB_PATH)}")
    except Exception as e:
        logger.error(f"Failed to initialize SQLite database: {e}")
        raise
    finally:
        conn.close()


# Initialise on import
init_db()
