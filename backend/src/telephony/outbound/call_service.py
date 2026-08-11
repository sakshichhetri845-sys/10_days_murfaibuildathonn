"""
Outbound call tracking & history service.
Handles SQLite operations for scheduled and immediate outbound calls.
"""

import logging
import uuid
from datetime import datetime
from datetime import timezone as dt_timezone
from typing import Any, Optional

try:
    from src.database import get_db_connection
except ImportError:
    from database import get_db_connection

logger = logging.getLogger("telephony.outbound.call_service")


def mask_phone_number(destination: str) -> str:
    """Mask phone number, Linphone username, or SIP URI for privacy preservation."""
    cleaned = destination.strip()
    if not cleaned:
        return ""
    if cleaned.startswith("sip:"):
        parts = cleaned.replace("sip:", "").split("@")
        user_part = parts[0]
        domain_part = parts[1] if len(parts) > 1 else ""
        masked_user = user_part[:3] + "***" if len(user_part) > 3 else user_part + "***"
        return (
            f"sip:{masked_user}@{domain_part}" if domain_part else f"sip:{masked_user}"
        )
    if (
        cleaned.startswith("+")
        or cleaned.isdigit()
        or (cleaned.startswith("1") and len(cleaned) >= 10)
    ):
        if len(cleaned) <= 6:
            return cleaned
        return f"{cleaned[:3]} **** {cleaned[-4:]}"
    if len(cleaned) <= 3:
        return cleaned + "***"
    return f"{cleaned[:3]}***"


class OutboundCallService:
    @staticmethod
    def create_call_record(
        phone_number: str,
        scheduled_time: Optional[str] = None,
        timezone_name: Optional[str] = None,
        status: str = "scheduled",
        room_name: Optional[str] = None,
        user_id: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> dict[str, Any]:
        """Creates a new outbound call record in the database."""
        tz_val = timezone or timezone_name or "UTC"
        call_id = f"call_{uuid.uuid4().hex[:12]}"
        now = datetime.now(dt_timezone.utc).isoformat()

        target_room = room_name or f"outbound-followup-{call_id[:8]}"

        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO outbound_calls (
                    call_id, phone_number, scheduled_time, timezone,
                    status, room_name, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    phone_number,
                    scheduled_time or now,
                    tz_val,
                    status,
                    target_room,
                    now,
                    now,
                ),
            )
            conn.commit()
            logger.info(
                f"Created call record: call_id={call_id}, phone={phone_number}, room={target_room}, user_id={user_id}"
            )
            return {
                "call_id": call_id,
                "phone_number": phone_number,
                "scheduled_time": scheduled_time or now,
                "timezone": tz_val,
                "status": status,
                "room_name": target_room,
                "user_id": user_id or "default_user",
                "created_at": now,
                "updated_at": now,
            }
        except Exception as e:
            logger.error(f"Failed to create call record for phone={phone_number}: {e}")
            return {}
        finally:
            conn.close()

    @staticmethod
    def update_call_status(
        call_id: str,
        status: str,
        participant_id: Optional[str] = None,
        room_name: Optional[str] = None,
    ) -> bool:
        """Updates the status of an existing call record."""
        now = datetime.now(dt_timezone.utc).isoformat()

        conn = get_db_connection()
        try:
            if participant_id:
                conn.execute(
                    """
                    UPDATE outbound_calls
                    SET status = ?, participant_id = ?, updated_at = ?
                    WHERE call_id = ?
                    """,
                    (status, participant_id, now, call_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE outbound_calls
                    SET status = ?, updated_at = ?
                    WHERE call_id = ?
                    """,
                    (status, now, call_id),
                )
            conn.commit()
            logger.info(f"Updated call_id={call_id} to status={status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update status for call_id={call_id}: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_call_history(limit: int = 20) -> list[dict[str, Any]]:
        """Returns recent call history records with masked phone numbers."""
        conn = get_db_connection()
        try:
            rows = conn.execute(
                """
                SELECT call_id, phone_number, scheduled_time, timezone,
                       status, room_name, participant_id, created_at
                FROM outbound_calls
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            history = []
            for r in rows:
                history.append(
                    {
                        "call_id": r["call_id"],
                        "phone_number": mask_phone_number(r["phone_number"]),
                        "raw_phone_number": r["phone_number"],
                        "scheduled_time": r["scheduled_time"],
                        "timezone": r["timezone"],
                        "status": r["status"],
                        "room_name": r["room_name"],
                        "participant_id": r["participant_id"],
                        "created_at": r["created_at"],
                    }
                )
            return history
        except Exception as e:
            logger.error(f"Failed to fetch call history: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_due_scheduled_calls() -> list[dict[str, Any]]:
        """Returns scheduled calls whose scheduled_time is due."""
        now = datetime.now(dt_timezone.utc).isoformat()

        conn = get_db_connection()
        try:
            rows = conn.execute(
                """
                SELECT call_id, phone_number, scheduled_time, timezone, room_name
                FROM outbound_calls
                WHERE status = 'scheduled' AND scheduled_time <= ?
                """,
                (now,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch due scheduled calls: {e}")
            return []
        finally:
            conn.close()
