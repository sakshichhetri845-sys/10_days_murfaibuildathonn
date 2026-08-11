"""
Database module for BolBuddy Voice Agent persistent memory storage.

Provides SQLite persistence for user identity, language preferences, learning-related facts,
and interaction timestamps. Designed to survive agent restarts, backend restarts, and new sessions.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("agent.db")

# Default database directory and file location inside backend
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DATA_DIR, "bolbuddy_memory.db")


def get_db_path(override_path: Optional[str] = None) -> str:
    """Get the active database file path."""
    if override_path:
        return override_path
    return os.getenv("BOLBUDDY_DB_PATH", DEFAULT_DB_PATH)


def _get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return an SQLite database connection with row factory configured."""
    active_path = get_db_path(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(active_path)), exist_ok=True)
    conn = sqlite3.connect(active_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> bool:
    """
    Initialize the SQLite database schema if it doesn't already exist.
    Creates the data directory and user_memory table safely.
    """
    try:
        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    language_preference TEXT,
                    facts TEXT DEFAULT '{}',
                    phone_number TEXT,
                    preferred_practice_time TEXT,
                    last_interaction TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Migration check for existing user_memory tables
            cursor.execute("PRAGMA table_info(user_memory)")
            existing_cols = [row["name"] for row in cursor.fetchall()]
            if "phone_number" not in existing_cols:
                cursor.execute("ALTER TABLE user_memory ADD COLUMN phone_number TEXT")
            if "preferred_practice_time" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE user_memory ADD COLUMN preferred_practice_time TEXT"
                )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scheduled_calls (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    status TEXT DEFAULT 'SCHEDULED',
                    attempt_count INTEGER DEFAULT 0,
                    last_attempt_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_schedules (
                    user_id TEXT PRIMARY KEY,
                    phone_number TEXT NOT NULL,
                    practice_topic TEXT NOT NULL DEFAULT 'Spoken English Practice',
                    preferred_time TEXT NOT NULL,
                    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    next_call_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            logger.info(
                f"Database schema initialized successfully at {get_db_path(db_path)}"
            )
            return True
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize SQLite database: {e}", exc_info=True)
        return False


def get_user(user_id: str, db_path: Optional[str] = None) -> Optional[dict[str, Any]]:
    """
    Retrieve a user's persistent memory record by user_id.

    Returns:
        dict containing user_id, name, language_preference, facts (as dict), last_interaction, etc.,
        or None if user does not exist or if a database error occurs.
    """
    if not user_id:
        logger.warning("get_user called with empty user_id")
        return None

    try:
        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id, name, language_preference, facts, phone_number, preferred_practice_time, last_interaction, created_at, updated_at
                FROM user_memory
                WHERE user_id = ?
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            user_dict = dict(row)
            # Deserialize facts JSON safely
            try:
                user_dict["facts"] = (
                    json.loads(user_dict["facts"]) if user_dict["facts"] else {}
                )
            except (json.JSONDecodeError, TypeError) as parse_err:
                logger.warning(
                    f"Failed to parse facts JSON for user {user_id}: {parse_err}"
                )
                user_dict["facts"] = {}

            return user_dict
    except sqlite3.Error as e:
        logger.error(
            f"Database error in get_user for user_id '{user_id}': {e}", exc_info=True
        )
        return None


def create_or_update_user(
    user_id: str,
    name: Optional[str] = None,
    language_preference: Optional[str] = None,
    facts: Optional[dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Create a new user memory record or update an existing record.
    Preserves existing fields if None is passed for optional arguments.

    Args:
        user_id: Unique persistent identifier for the user.
        name: User's preferred name.
        language_preference: Preferred language mode (e.g. "English + Hindi").
        facts: Structured dictionary of learning facts (e.g. level, goals, topics_practiced).
        db_path: Optional database path override.

    Returns:
        Updated user record as a dict, or None on failure.
    """
    if not user_id:
        logger.warning("create_or_update_user called with empty user_id")
        return None

    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        # Fetch existing record to merge fields cleanly if partial updates are passed
        existing_user = get_user(user_id, db_path=db_path)

        final_name = (
            name
            if name is not None
            else (existing_user.get("name") if existing_user else None)
        )
        final_lang = (
            language_preference
            if language_preference is not None
            else (existing_user.get("language_preference") if existing_user else None)
        )

        # Merge facts if existing facts exist
        if existing_user and existing_user.get("facts"):
            merged_facts = dict(existing_user["facts"])
            if facts:
                merged_facts.update(facts)
        else:
            merged_facts = facts or {}

        facts_json = json.dumps(merged_facts)

        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_memory (user_id, name, language_preference, facts, last_interaction, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name = COALESCE(excluded.name, user_memory.name),
                    language_preference = COALESCE(excluded.language_preference, user_memory.language_preference),
                    facts = excluded.facts,
                    last_interaction = excluded.last_interaction,
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    final_name,
                    final_lang,
                    facts_json,
                    now_iso,
                    now_iso,
                    now_iso,
                ),
            )
            conn.commit()

        logger.info(f"User record created/updated successfully for user_id: {user_id}")
        return get_user(user_id, db_path=db_path)
    except sqlite3.Error as e:
        logger.error(
            f"Database error in create_or_update_user for '{user_id}': {e}",
            exc_info=True,
        )
        return None


def update_last_interaction(user_id: str, db_path: Optional[str] = None) -> bool:
    """
    Update the last_interaction and updated_at timestamps for a given user_id.

    Returns:
        True if record was updated, False if user does not exist or database error occurred.
    """
    if not user_id:
        return False

    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE user_memory
                SET last_interaction = ?, updated_at = ?
                WHERE user_id = ?
                """,
                (now_iso, now_iso, user_id),
            )
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Updated last_interaction for user_id: {user_id}")
                return True
            else:
                logger.warning(
                    f"update_last_interaction: user_id '{user_id}' not found"
                )
                return False
    except sqlite3.Error as e:
        logger.error(
            f"Database error in update_last_interaction for '{user_id}': {e}",
            exc_info=True,
        )
        return False


def delete_user(user_id: str, db_path: Optional[str] = None) -> bool:
    """
    Delete a user record by user_id (useful for test cleanup or future forget functionality).

    Returns:
        True if deleted, False otherwise.
    """
    if not user_id:
        return False

    try:
        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_memory WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(
            f"Database error in delete_user for '{user_id}': {e}", exc_info=True
        )
        return False


def get_or_create_user(
    user_id: str,
    name: Optional[str] = None,
    language_preference: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Retrieve existing user record or create a new initial record if user does not exist yet.
    """
    existing = get_user(user_id, db_path=db_path)
    if existing:
        update_last_interaction(user_id, db_path=db_path)
        return get_user(user_id, db_path=db_path)

    return create_or_update_user(
        user_id=user_id,
        name=name,
        language_preference=language_preference,
        facts={
            "current_level": "beginner",
            "learning_goal": "everyday conversation",
            "topics_practiced": [],
            "recurring_challenges": [],
        },
        db_path=db_path,
    )


def record_learning_progress(
    user_id: str,
    current_level: Optional[str] = None,
    learning_goal: Optional[str] = None,
    topics_practiced: Optional[list[str]] = None,
    recurring_challenges: Optional[list[str]] = None,
    db_path: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Helper to update a user's learning facts while preserving existing topics and challenges.
    Appends new unique topics and challenges to existing lists.
    """
    user = get_user(user_id, db_path=db_path)
    if not user:
        user = create_or_update_user(user_id=user_id, db_path=db_path)
        if not user:
            return None

    existing_facts = user.get("facts") or {}

    new_facts = dict(existing_facts)

    if current_level is not None:
        new_facts["current_level"] = current_level

    if learning_goal is not None:
        new_facts["learning_goal"] = learning_goal

    # Deduplicate and append topics
    if topics_practiced:
        current_topics = list(new_facts.get("topics_practiced", []))
        for topic in topics_practiced:
            if topic and topic not in current_topics:
                current_topics.append(topic)
        new_facts["topics_practiced"] = current_topics

    # Deduplicate and append challenges
    if recurring_challenges:
        current_challenges = list(new_facts.get("recurring_challenges", []))
        for challenge in recurring_challenges:
            if challenge and challenge not in current_challenges:
                current_challenges.append(challenge)
        new_facts["recurring_challenges"] = current_challenges

    return create_or_update_user(user_id=user_id, facts=new_facts, db_path=db_path)


def save_learner_outbound_preferences(
    user_id: str,
    phone_number: str,
    preferred_practice_time: str,
    name: Optional[str] = None,
    db_path: Optional[str] = None,
) -> bool:
    """Save user's phone number and preferred practice time in persistent database."""
    if not user_id or not phone_number:
        return False
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_memory (user_id, name, phone_number, preferred_practice_time, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name = COALESCE(excluded.name, user_memory.name),
                    phone_number = excluded.phone_number,
                    preferred_practice_time = excluded.preferred_practice_time,
                    updated_at = excluded.updated_at
                """,
                (user_id, name, phone_number, preferred_practice_time, now_iso),
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(
            f"Failed to save learner outbound preferences for '{user_id}': {e}",
            exc_info=True,
        )
        return False


def create_scheduled_call(
    user_id: str,
    phone_number: str,
    scheduled_time: str,
    db_path: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Create a new scheduled practice call entry."""
    import uuid

    if not user_id or not phone_number:
        return None
    call_id = f"call_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scheduled_calls (id, user_id, phone_number, scheduled_time, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'SCHEDULED', ?, ?)
                """,
                (call_id, user_id, phone_number, scheduled_time, now_iso, now_iso),
            )
            conn.commit()
        return {
            "id": call_id,
            "user_id": user_id,
            "phone_number": phone_number,
            "scheduled_time": scheduled_time,
            "status": "SCHEDULED",
            "attempt_count": 0,
            "created_at": now_iso,
        }
    except sqlite3.Error as e:
        logger.error(
            f"Failed to create scheduled call for '{user_id}': {e}", exc_info=True
        )
        return None


def get_scheduled_calls(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    db_path: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Retrieve scheduled call records filtered by user_id or status."""
    try:
        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            query = "SELECT id, user_id, phone_number, scheduled_time, status, attempt_count, last_attempt_at, created_at, updated_at FROM scheduled_calls"
            params = []
            conditions = []
            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
            if status:
                conditions.append("status = ?")
                params.append(status)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get scheduled calls: {e}", exc_info=True)
        return []


def update_call_status(
    call_id: str,
    status: str,
    increment_attempt: bool = False,
    db_path: Optional[str] = None,
) -> bool:
    """Update scheduled call status and optionally increment attempt count."""
    if not call_id:
        return False
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            if increment_attempt:
                cursor.execute(
                    """
                    UPDATE scheduled_calls
                    SET status = ?, attempt_count = attempt_count + 1, last_attempt_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, now_iso, now_iso, call_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE scheduled_calls
                    SET status = ?, last_attempt_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, now_iso, now_iso, call_id),
                )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(
            f"Failed to update call status for '{call_id}': {e}", exc_info=True
        )
        return False
