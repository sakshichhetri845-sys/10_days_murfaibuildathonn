"""
Schedule Model Module for BolBuddy Voice Agent.

Manages persistent daily practice call schedules in SQLite (bolbuddy_memory.db).
Handles time parsing, timezone calculations, phone validation, and CRUD actions.
"""

import logging
import re
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from db import _get_connection, init_db

logger = logging.getLogger("agent.schedule_model")


def parse_time_str(time_str: str) -> tuple[int, int]:
    """
    Parse preferred time string into (hour, minute).
    Supports formats like '20:00', '8:00 PM', '08:30 AM', '19:45'.
    """
    if not time_str or not time_str.strip():
        raise ValueError("Preferred practice time must be provided.")

    cleaned = time_str.strip().upper()

    # 12-hour format with AM/PM (e.g. "8:00 PM", "08:30AM")
    am_pm_match = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM)$", cleaned)
    if am_pm_match:
        hr, mn, period = am_pm_match.groups()
        hour = int(hr)
        minute = int(mn)
        if not (1 <= hour <= 12 and 0 <= minute <= 59):
            raise ValueError(f"Invalid time value in '{time_str}'")
        if period == "PM" and hour < 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0
        return hour, minute

    # 24-hour format (e.g. "20:00", "08:30")
    military_match = re.match(r"^(\d{1,2}):(\d{2})$", cleaned)
    if military_match:
        hr, mn = military_match.groups()
        hour = int(hr)
        minute = int(mn)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Invalid time value in '{time_str}'")
        return hour, minute

    raise ValueError(
        f"Unrecognized time format '{time_str}'. Use HH:MM or HH:MM AM/PM."
    )


def validate_phone_number(phone_number: str) -> str:
    """Validate and clean phone number format."""
    if not phone_number or not phone_number.strip():
        raise ValueError("Phone number must be provided.")

    cleaned = phone_number.strip()
    digits = re.sub(r"[^\d]", "", cleaned)
    if len(digits) < 7 or len(digits) > 15:
        raise ValueError(
            "Phone number must contain between 7 and 15 digits (e.g. +919876543210)."
        )
    return cleaned


def resolve_timezone(tz_name: Optional[str]) -> tuple[ZoneInfo, str]:
    """Resolve timezone or fall back to Asia/Kolkata if unspecified/invalid."""
    if not tz_name or not tz_name.strip():
        return ZoneInfo("Asia/Kolkata"), "Asia/Kolkata"

    tz_str = tz_name.strip()
    try:
        return ZoneInfo(tz_str), tz_str
    except (ZoneInfoNotFoundError, Exception):
        logger.warning(
            f"Invalid timezone '{tz_str}' specified; falling back to Asia/Kolkata."
        )
        return ZoneInfo("Asia/Kolkata"), "Asia/Kolkata"


def calculate_next_call_at(
    preferred_time: str,
    tz_str: str,
    from_dt: Optional[datetime] = None,
) -> str:
    """
    Calculate the next occurrence ISO 8601 UTC timestamp for a daily practice call.
    """
    hour, minute = parse_time_str(preferred_time)
    tz, _resolved_tz_name = resolve_timezone(tz_str)

    now_local = (from_dt or datetime.now(dt_timezone.utc)).astimezone(tz)

    target_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if target_local <= now_local:
        target_local += timedelta(days=1)

    return target_local.astimezone(dt_timezone.utc).isoformat()


def create_or_update_schedule(
    user_id: str,
    phone_number: str,
    practice_topic: str = "Spoken English Practice",
    preferred_time: str = "20:00",
    timezone: str = "Asia/Kolkata",
    enabled: bool = True,
    test_delay_seconds: Optional[int] = None,
    db_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    CREATE or UPDATE daily schedule record in SQLite database.
    Supports test_delay_seconds (e.g., 60 for 'Call in 1 minute' dev mode).
    """
    if not user_id or not user_id.strip():
        raise ValueError("user_id must be provided.")

    init_db(db_path)

    clean_phone = validate_phone_number(phone_number)
    parse_time_str(preferred_time)
    _, valid_tz_str = resolve_timezone(timezone)

    if test_delay_seconds is not None and test_delay_seconds >= 0:
        next_call_at = (
            datetime.now(dt_timezone.utc) + timedelta(seconds=test_delay_seconds)
        ).isoformat()
    else:
        next_call_at = calculate_next_call_at(preferred_time, valid_tz_str)

    topic = practice_topic.strip() or "Spoken English Practice"
    is_enabled = 1 if enabled else 0

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO daily_schedules (
                user_id, phone_number, practice_topic, preferred_time,
                timezone, enabled, next_call_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                phone_number = excluded.phone_number,
                practice_topic = excluded.practice_topic,
                preferred_time = excluded.preferred_time,
                timezone = excluded.timezone,
                enabled = excluded.enabled,
                next_call_at = excluded.next_call_at,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id.strip(),
                clean_phone,
                topic,
                preferred_time.strip(),
                valid_tz_str,
                is_enabled,
                next_call_at,
            ),
        )
        conn.commit()

    return get_schedule(user_id, db_path=db_path) or {}


def get_schedule(
    user_id: str, db_path: Optional[str] = None
) -> Optional[dict[str, Any]]:
    """GET current daily schedule for user_id."""
    if not user_id or not user_id.strip():
        return None

    init_db(db_path)

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, phone_number, practice_topic, preferred_time,
                   timezone, enabled, next_call_at, created_at, updated_at
            FROM daily_schedules
            WHERE user_id = ?
            """,
            (user_id.strip(),),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "user_id": row["user_id"],
            "phone_number": row["phone_number"],
            "practice_topic": row["practice_topic"],
            "preferred_time": row["preferred_time"],
            "timezone": row["timezone"],
            "enabled": bool(row["enabled"]),
            "next_call_at": row["next_call_at"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def cancel_schedule(user_id: str, db_path: Optional[str] = None) -> bool:
    """CANCEL / disable current daily schedule for user_id."""
    if not user_id or not user_id.strip():
        return False

    init_db(db_path)

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE daily_schedules
            SET enabled = 0, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (user_id.strip(),),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_due_schedules(db_path: Optional[str] = None) -> list[dict[str, Any]]:
    """Retrieve all enabled schedules where next_call_at <= now (UTC)."""
    init_db(db_path)
    now_iso = datetime.now(dt_timezone.utc).isoformat()

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, phone_number, practice_topic, preferred_time,
                   timezone, enabled, next_call_at, created_at, updated_at
            FROM daily_schedules
            WHERE enabled = 1 AND next_call_at <= ?
            """,
            (now_iso,),
        )
        rows = cursor.fetchall()
        return [
            {
                "user_id": row["user_id"],
                "phone_number": row["phone_number"],
                "practice_topic": row["practice_topic"],
                "preferred_time": row["preferred_time"],
                "timezone": row["timezone"],
                "enabled": bool(row["enabled"]),
                "next_call_at": row["next_call_at"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


def update_schedule_next_occurrence(
    user_id: str, db_path: Optional[str] = None
) -> Optional[dict[str, Any]]:
    """Calculate and set next occurrence for tomorrow after a schedule triggers."""
    sched = get_schedule(user_id, db_path=db_path)
    if not sched:
        return None

    next_iso = calculate_next_call_at(sched["preferred_time"], sched["timezone"])

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE daily_schedules
            SET next_call_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (next_iso, user_id.strip()),
        )
        conn.commit()

    return get_schedule(user_id, db_path=db_path)
