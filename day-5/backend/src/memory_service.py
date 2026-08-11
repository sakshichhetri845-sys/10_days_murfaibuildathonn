"""
Memory Service module for HealthSaathi Voice Agent.
CRUD operations against SQLite with proper connection cleanup.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

try:
    from src.database import get_db_connection
except ImportError:
    from database import get_db_connection

logger = logging.getLogger("healthsathi.memory_service")


class MemoryService:
    @staticmethod
    def get_memory(user_id: str) -> Optional[dict[str, Any]]:
        if not user_id:
            return None
        conn = get_db_connection()
        try:
            row = conn.execute(
                """
                SELECT user_id, name, age_band, language_preference,
                       ongoing_conditions, last_triage_outcome, last_interaction
                FROM user_memories WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        except Exception as e:
            logger.error(
                f"Error reading memory for user_id={user_id}: {e}", exc_info=True
            )
            return None
        finally:
            conn.close()

        if not row:
            return None

        conditions: list[str] = []
        if row["ongoing_conditions"]:
            try:
                conditions = json.loads(row["ongoing_conditions"])
            except Exception:
                conditions = []

        logger.info(f"Memory lookup OK for user_id={user_id}")
        return {
            "user_id": row["user_id"],
            "name": row["name"],
            "age_band": row["age_band"],
            "language_preference": row["language_preference"],
            "ongoing_conditions": conditions,
            "last_triage_outcome": row["last_triage_outcome"],
            "last_interaction": row["last_interaction"],
        }

    @staticmethod
    def save_memory(
        user_id: str,
        name: Optional[str] = None,
        age_band: Optional[str] = None,
        language_preference: Optional[str] = None,
        ongoing_conditions: Optional[list[str]] = None,
        last_triage_outcome: Optional[str] = None,
    ) -> bool:
        if not user_id:
            logger.error("Cannot save memory: user_id is missing")
            return False

        # Merge with existing record so partial updates don't wipe other fields
        existing = MemoryService.get_memory(user_id) or {}
        merged = {
            "name": name if name is not None else existing.get("name"),
            "age_band": age_band if age_band is not None else existing.get("age_band"),
            "language_preference": (
                language_preference
                if language_preference is not None
                else existing.get("language_preference")
            ),
            "ongoing_conditions": (
                ongoing_conditions
                if ongoing_conditions is not None
                else existing.get("ongoing_conditions", [])
            ),
            "last_triage_outcome": (
                last_triage_outcome
                if last_triage_outcome is not None
                else existing.get("last_triage_outcome")
            ),
        }
        now = datetime.now(timezone.utc).isoformat()
        conditions_json = json.dumps(merged["ongoing_conditions"])

        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO user_memories (
                    user_id, name, age_band, language_preference,
                    ongoing_conditions, last_triage_outcome, last_interaction, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name                = excluded.name,
                    age_band            = excluded.age_band,
                    language_preference = excluded.language_preference,
                    ongoing_conditions  = excluded.ongoing_conditions,
                    last_triage_outcome = excluded.last_triage_outcome,
                    last_interaction    = excluded.last_interaction,
                    updated_at          = excluded.updated_at
                """,
                (
                    user_id,
                    merged["name"],
                    merged["age_band"],
                    merged["language_preference"],
                    conditions_json,
                    merged["last_triage_outcome"],
                    now,
                    now,
                ),
            )
            conn.commit()
            logger.info(f"Memory saved for user_id={user_id}")
            return True
        except Exception as e:
            logger.error(
                f"Error saving memory for user_id={user_id}: {e}", exc_info=True
            )
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_memory(user_id: str) -> bool:
        if not user_id:
            logger.error("Cannot delete memory: user_id missing")
            return False
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM user_memories WHERE user_id = ?", (user_id,))
            conn.commit()
            logger.info(f"Memory deleted for user_id={user_id}")
            return True
        except Exception as e:
            logger.error(
                f"Error deleting memory for user_id={user_id}: {e}", exc_info=True
            )
            return False
        finally:
            conn.close()

    @staticmethod
    def format_memory_summary(memory: Optional[dict[str, Any]]) -> str:
        if not memory:
            return "No prior memory recorded for this user."
        parts = []
        if memory.get("name"):
            parts.append(f"Name: {memory['name']}")
        if memory.get("age_band"):
            parts.append(f"Age band: {memory['age_band']}")
        if memory.get("language_preference"):
            parts.append(f"Preferred language: {memory['language_preference']}")
        if memory.get("ongoing_conditions"):
            parts.append(
                f"Ongoing conditions (consented): {', '.join(memory['ongoing_conditions'])}"
            )
        if memory.get("last_triage_outcome"):
            parts.append(f"Previous guidance: {memory['last_triage_outcome']}")
        if memory.get("last_interaction"):
            parts.append(f"Last interaction: {memory['last_interaction']}")
        return "\n".join(parts) if parts else "No prior memory recorded for this user."
