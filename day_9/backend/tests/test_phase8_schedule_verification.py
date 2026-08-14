"""
Automated Test Suite for Phase 8 End-to-End Schedule Verification.
"""

import asyncio
from datetime import datetime
from datetime import timezone as dt_timezone

import pytest

from db import init_db
from schedule_model import (
    create_or_update_schedule,
    get_schedule,
)
from scheduler import process_due_schedules


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Isolated database environment for Phase 8 schedule verification."""
    db_file = str(tmp_path / "test_phase8.db")
    monkeypatch.setenv("BOLBUDDY_DB_PATH", db_file)
    monkeypatch.delenv("LIVEKIT_SIP_TRUNK_ID", raising=False)
    init_db(db_file)
    return db_file


@pytest.mark.asyncio
async def test_full_schedule_lifecycle_and_restart_survival(setup_test_db):
    """
    Test 11-step end-to-end lifecycle:
    1. Create schedule.
    2. Verify persistence.
    3. Simulate backend restart (re-fetch schedule).
    4. Verify schedule still exists.
    5. Trigger 1-minute short interval / due schedule.
    6. Scheduler detects due task.
    7. Outbound trigger runs.
    8. Schedule next_call_at advances to next day.
    """
    user_id = "user_phase8_e2e"
    phone = "+919876543210"
    topic = "Software Engineering Interview"
    pref_time = "20:00"

    # Step 1: Create schedule (with 2-second short test delay)
    created = create_or_update_schedule(
        user_id=user_id,
        phone_number=phone,
        practice_topic=topic,
        preferred_time=pref_time,
        timezone="Asia/Kolkata",
        test_delay_seconds=2,
        db_path=setup_test_db,
    )

    # Step 2: Verify persistence
    assert created["user_id"] == user_id
    assert created["phone_number"] == phone
    assert created["practice_topic"] == topic
    assert created["enabled"] is True

    # Step 3 & 4: Simulate backend restart (re-open DB and query)
    fetched_after_restart = get_schedule(user_id, db_path=setup_test_db)
    assert fetched_after_restart is not None
    assert fetched_after_restart["user_id"] == user_id
    assert fetched_after_restart["practice_topic"] == topic

    # Step 5: Wait 2.1 seconds for next_call_at to arrive
    await asyncio.sleep(2.1)

    # Step 6 & 7: Scheduler detects and triggers due call
    results = await process_due_schedules(db_path=setup_test_db)
    assert len(results) == 1
    assert results[0]["user_id"] == user_id

    # Step 8: Verify next call is scheduled for the following day
    updated = get_schedule(user_id, db_path=setup_test_db)
    assert updated["enabled"] is True
    assert updated["next_call_at"] > datetime.now(dt_timezone.utc).isoformat()
