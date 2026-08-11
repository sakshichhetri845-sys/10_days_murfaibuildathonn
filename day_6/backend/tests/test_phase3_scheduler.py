"""
Unit tests for Phase 3 Persistent Background Scheduler.
"""

from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

import pytest

from schedule_model import create_or_update_schedule, get_schedule
from scheduler import process_due_schedules


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Isolated database environment for scheduler tests."""
    db_file = str(tmp_path / "test_scheduler.db")
    monkeypatch.setenv("BOLBUDDY_DB_PATH", db_file)
    monkeypatch.delenv("LIVEKIT_SIP_TRUNK_ID", raising=False)
    return db_file


@pytest.mark.asyncio
async def test_process_due_schedules_triggers_and_advances(setup_test_db, monkeypatch):
    """Verify due schedules trigger outbound call, advance next_call_at, and survive errors."""
    monkeypatch.delenv("LIVEKIT_SIP_TRUNK_ID", raising=False)
    monkeypatch.delenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID", raising=False)
    user_id = "sched_user_due"
    create_or_update_schedule(
        user_id=user_id,
        phone_number="+919876543210",
        practice_topic="Mock Interview Practice",
        preferred_time="20:00",
        timezone="Asia/Kolkata",
        db_path=setup_test_db,
    )

    # Force next_call_at into the past (5 minutes ago)
    past_iso = (datetime.now(dt_timezone.utc) - timedelta(minutes=5)).isoformat()
    from db import _get_connection

    with _get_connection(setup_test_db) as conn:
        conn.execute(
            "UPDATE daily_schedules SET next_call_at = ? WHERE user_id = ?",
            (past_iso, user_id),
        )
        conn.commit()

    # Process due schedules
    results = await process_due_schedules(db_path=setup_test_db)

    assert len(results) == 1
    res = results[0]
    assert res["user_id"] == user_id
    # Call attempt recorded as PROVIDER_ERROR because SIP Trunk ID is not set in test environment
    assert res["status"] == "PROVIDER_ERROR"

    # Verify schedule next_call_at was advanced to future occurrence
    updated_sched = get_schedule(user_id, db_path=setup_test_db)
    assert updated_sched["next_call_at"] > datetime.now(dt_timezone.utc).isoformat()
