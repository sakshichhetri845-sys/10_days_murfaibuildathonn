"""
Outbound Practice Call Trigger and Scheduler Module for BolBuddy Voice Agent.

Provides schedule registration, manual test triggers for dev/testing,
and outbound call dispatch management integrated with persistent memory.
"""

import logging
import time
from typing import Any, Optional

from db import (
    create_scheduled_call,
    get_user,
    save_learner_outbound_preferences,
    update_call_status,
)
from telephony import (
    TelephonyConfigurationError,
    get_telephony_config,
    initiate_outbound_call,
    mask_phone_number,
)

logger = logging.getLogger("agent.outbound")


def schedule_outbound_practice(
    user_id: str,
    phone_number: str,
    scheduled_time: str,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Register a learner's preferred practice time and phone number for outbound calling.
    Saves preferences and creates a scheduled call entry.
    """
    if not user_id or not user_id.strip():
        raise ValueError("user_id is required for scheduling practice calls.")
    if not phone_number or not phone_number.strip():
        raise ValueError("phone_number is required for scheduling practice calls.")
    if not scheduled_time or not scheduled_time.strip():
        raise ValueError("scheduled_time is required for scheduling practice calls.")

    uid = user_id.strip()
    phone = phone_number.strip()
    sched = scheduled_time.strip()

    # Save to user memory table
    save_learner_outbound_preferences(
        user_id=uid,
        phone_number=phone,
        preferred_practice_time=sched,
        name=name,
    )

    # Save to scheduled calls table
    scheduled_record = create_scheduled_call(
        user_id=uid,
        phone_number=phone,
        scheduled_time=sched,
    )

    masked_phone = mask_phone_number(phone)
    logger.info(
        f"Scheduled practice call for user_id='{uid}', phone='{masked_phone}', scheduled_time='{sched}'"
    )

    return {
        "success": True,
        "call_id": scheduled_record["id"] if scheduled_record else None,
        "user_id": uid,
        "phone_number_masked": masked_phone,
        "scheduled_time": sched,
        "status": "SCHEDULED",
    }


async def trigger_outbound_practice(
    user_id: str,
    phone_number: Optional[str] = None,
    name: Optional[str] = None,
    room_name: Optional[str] = None,
    practice_topic: Optional[str] = None,
    db_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    Manual test trigger for development to initiate an outbound practice call immediately.
    If phone_number is not supplied, looks up stored phone_number from learner DB record.
    """
    if not user_id or not user_id.strip():
        raise ValueError("user_id is required to trigger outbound practice call.")

    uid = user_id.strip()
    user_record = get_user(uid)

    target_name = name or (user_record.get("name") if user_record else None) or uid
    target_phone = phone_number or (
        user_record.get("phone_number") if user_record else None
    )

    if not target_phone or not str(target_phone).strip():
        raise ValueError(
            f"No phone number provided or stored in DB record for user_id '{uid}'."
        )

    clean_phone = str(target_phone).strip()
    active_room = room_name or f"bolbuddy_outbound_{uid}_{int(time.time())}"

    # Log scheduled call trigger attempt in DB
    sched_record = create_scheduled_call(
        user_id=uid,
        phone_number=clean_phone,
        scheduled_time="IMMEDIATE_TEST_TRIGGER",
    )
    call_id = sched_record["id"] if sched_record else f"call_test_{int(time.time())}"

    masked_phone = mask_phone_number(clean_phone)
    logger.info(
        f"Manual test trigger initiating call for user_id='{uid}', room='{active_room}'"
    )

    try:
        call_res = await initiate_outbound_call(
            phone_number=clean_phone,
            room_name=active_room,
            user_id=uid,
            user_name=target_name,
        )

        update_call_status(call_id, "CALLING", increment_attempt=True)

        return {
            "success": True,
            "call_id": call_id,
            "user_id": uid,
            "name": target_name,
            "phone_number_masked": masked_phone,
            "room_name": active_room,
            "status": "CALLING",
            "telephony_details": call_res,
        }

    except TelephonyConfigurationError as config_err:
        update_call_status(call_id, "PROVIDER_ERROR", increment_attempt=True)
        logger.warning(
            f"Outbound trigger blocked due to missing configuration: {config_err}"
        )
        return {
            "success": False,
            "call_id": call_id,
            "user_id": uid,
            "phone_number_masked": masked_phone,
            "status": "PROVIDER_ERROR",
            "error": str(config_err),
            "missing_config": get_telephony_config().get("missing_vars", []),
        }

    except Exception as err:
        update_call_status(call_id, "PROVIDER_ERROR", increment_attempt=True)
        logger.error(f"Outbound trigger failed: {err}", exc_info=True)
        return {
            "success": False,
            "call_id": call_id,
            "user_id": uid,
            "phone_number_masked": masked_phone,
            "status": "PROVIDER_ERROR",
            "error": str(err),
        }


VALID_CALL_OUTCOMES = {
    "COMPLETED",
    "DECLINED",
    "BUSY",
    "NO_ANSWER",
    "VOICEMAIL",
    "IMMEDIATE_HANGUP",
    "CALL_ENDED",
    "PROVIDER_ERROR",
}


def record_call_outcome(
    call_id: str,
    outcome: str,
    user_id: Optional[str] = None,
    details: Optional[str] = None,
) -> dict[str, Any]:
    """
    Log and store call outcome in persistent SQLite database.
    Supports all explicit Day 6 outcomes: COMPLETED, DECLINED, BUSY, NO_ANSWER, VOICEMAIL, IMMEDIATE_HANGUP, PROVIDER_ERROR.
    """
    normalized = outcome.upper().strip() if outcome else "PROVIDER_ERROR"
    if normalized not in VALID_CALL_OUTCOMES:
        logger.warning(
            f"Unrecognized call outcome '{outcome}', mapping to PROVIDER_ERROR"
        )
        normalized = "PROVIDER_ERROR"

    user_info = f" for user_id '{user_id}'" if user_id else ""
    logger.info(f"CALL OUTCOME LOGGED: {normalized}{user_info} (call_id: '{call_id}')")

    success = update_call_status(call_id, normalized)

    return {
        "success": success,
        "call_id": call_id,
        "user_id": user_id,
        "outcome": normalized,
        "details": details or "",
    }


def get_retry_config() -> dict[str, int]:
    """Retrieve retry policy configuration parameters from environment variables."""
    import os

    try:
        max_retries = int(os.getenv("OUTBOUND_MAX_RETRIES", "1"))
    except ValueError:
        max_retries = 1

    try:
        retry_delay = int(os.getenv("OUTBOUND_RETRY_DELAY_SECONDS", "300"))
    except ValueError:
        retry_delay = 300

    return {
        "max_retries": max(0, max_retries),
        "retry_delay_seconds": max(0, retry_delay),
    }


def should_retry_call(call_record: dict[str, Any]) -> tuple[bool, str]:
    """
    Evaluate conservative retry policy for a given scheduled practice call.

    Rules:
    1. If user explicitly DECLINED or CANCELLED: NO RETRY.
    2. If session COMPLETED: NO RETRY.
    3. If attempt_count > max_retries: NO RETRY.
    4. If inside retry delay window: NO IMMEDIATE RETRY (must wait delay window).
    5. Only transient failures (NO_ANSWER, BUSY, PROVIDER_ERROR) after delay are retryable.
    """
    if not call_record:
        return False, "Call record invalid or not found."

    status = (call_record.get("status") or "").upper().strip()
    attempt_count = call_record.get("attempt_count", 0)
    last_attempt_at = call_record.get("last_attempt_at")

    config = get_retry_config()
    max_retries = config["max_retries"]
    delay_seconds = config["retry_delay_seconds"]

    if status == "DECLINED":
        return False, "User explicitly declined practice call. Immediate retry blocked."

    if status in ("CANCELLED", "OPTED_OUT"):
        return False, "User opted out of practice calls. Future calls cancelled."

    if status == "COMPLETED":
        return False, "Practice session completed successfully. No retry required."

    if attempt_count > max_retries:
        return (
            False,
            f"Maximum retry attempts reached ({attempt_count}/{max_retries}).",
        )

    # Enforce retry delay window
    if last_attempt_at:
        try:
            from datetime import datetime, timezone

            last_dt = datetime.fromisoformat(last_attempt_at.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            elapsed = (now_dt - last_dt).total_seconds()
            if elapsed < delay_seconds:
                remaining = int(delay_seconds - elapsed)
                return (
                    False,
                    f"Immediate retry blocked. Retry delay window active ({remaining}s remaining).",
                )
        except Exception as e:
            logger.warning(
                f"Error parsing last_attempt_at timestamp '{last_attempt_at}': {e}"
            )

    if status in ("NO_ANSWER", "BUSY", "PROVIDER_ERROR", "IMMEDIATE_HANGUP"):
        return True, "Eligible for conservative retry."

    return False, f"Status '{status}' is not eligible for retry."


def opt_out_user_from_practice_calls(
    user_id: str, db_path: Optional[str] = None
) -> dict[str, Any]:
    """
    Cancel future scheduled practice calls for user when they say 'don't call me' or opt out.
    """
    from db import get_scheduled_calls

    if not user_id or not user_id.strip():
        raise ValueError("user_id is required for opt-out operation.")
    uid = user_id.strip()

    # Cancel all future scheduled calls for this user in DB
    calls = get_scheduled_calls(user_id=uid, status="SCHEDULED", db_path=db_path)
    cancelled_count = 0
    for call in calls:
        if update_call_status(call["id"], "CANCELLED", db_path=db_path):
            cancelled_count += 1

    # Save opt-out state in user_memory DB record
    save_learner_outbound_preferences(
        user_id=uid,
        phone_number="",
        preferred_practice_time="OPTED_OUT",
        db_path=db_path,
    )

    logger.info(
        f"User '{uid}' opted out. Cancelled {cancelled_count} future scheduled calls."
    )
    return {
        "success": True,
        "user_id": uid,
        "opted_out": True,
        "cancelled_scheduled_calls": cancelled_count,
    }


if __name__ == "__main__":
    import asyncio
    import json
    import sys

    logging.basicConfig(level=logging.INFO)

    args = sys.argv[1:]
    if len(args) >= 2 and args[0] in ("test-call", "test_call", "call"):
        target_phone = args[1]
        user_id = args[2] if len(args) >= 3 else "test_user_cli"
        print(f"Initiating manual test call to {target_phone} for user '{user_id}'...")
        res = asyncio.run(
            trigger_outbound_practice(user_id=user_id, phone_number=target_phone)
        )
        print("Result:", json.dumps(res, indent=2))
    else:
        print("Usage: python -m outbound test-call <phone_number> [user_id]")
        sys.exit(1)
