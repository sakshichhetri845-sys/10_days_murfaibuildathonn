"""
Persistent Background Scheduler for BolBuddy Voice Agent.

Polls SQLite database every N seconds (default 15s) for due daily practice call schedules.
Triggers LiveKit outbound calls, calculates next daily occurrence, and handles errors gracefully.
"""

import asyncio
import logging
from typing import Any, Optional

from outbound import trigger_outbound_practice
from schedule_model import (
    get_due_schedules,
    update_schedule_next_occurrence,
)

logger = logging.getLogger("agent.scheduler")


async def process_due_schedules(db_path: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Find due schedules (next_call_at <= now), trigger outbound call, and advance to next daily occurrence.
    Survives restarts because schedule state is persisted in SQLite.
    """
    due_list = get_due_schedules(db_path=db_path)
    results = []

    for sched in due_list:
        user_id = sched["user_id"]
        phone_number = sched["phone_number"]
        practice_topic = sched.get("practice_topic", "Spoken English Practice")

        logger.info(
            f"Scheduler triggering due daily practice call for user '{user_id}' (Topic: {practice_topic})"
        )

        try:
            # Trigger existing LiveKit outbound SIP call integration
            res = await trigger_outbound_practice(
                user_id=user_id,
                phone_number=phone_number,
                practice_topic=practice_topic,
                db_path=db_path,
            )
            results.append(res)
        except Exception as err:
            logger.error(
                f"Scheduler error triggering call for user '{user_id}': {err}",
                exc_info=True,
            )
            results.append({"user_id": user_id, "success": False, "error": str(err)})

        # Always advance next_call_at to next daily occurrence so failures don't loop continuously
        try:
            updated = update_schedule_next_occurrence(user_id, db_path=db_path)
            logger.info(
                f"Advanced schedule for user '{user_id}'. Next call at: {updated.get('next_call_at') if updated else 'N/A'}"
            )
        except Exception as update_err:
            logger.error(
                f"Failed to update next occurrence for user '{user_id}': {update_err}"
            )

    return results


async def start_scheduler_loop(
    poll_interval_seconds: float = 15.0, db_path: Optional[str] = None
) -> None:
    """
    Background polling loop. Runs with short sleep intervals (e.g. 15s) to check due tasks.
    """
    logger.info(
        f"BolBuddy Daily Practice Scheduler started (Polling every {poll_interval_seconds}s)"
    )
    while True:
        try:
            await process_due_schedules(db_path=db_path)
        except Exception as loop_err:
            logger.error(f"Error in scheduler polling loop: {loop_err}", exc_info=True)

        await asyncio.sleep(poll_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting standalone BolBuddy Daily Scheduler...")
    try:
        asyncio.run(start_scheduler_loop())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")
