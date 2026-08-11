"""
Tests for Outbound Call Trigger & Scheduler Module (Phase 3).
"""

import pytest

from db import get_scheduled_calls, get_user, init_db
from outbound import schedule_outbound_practice, trigger_outbound_practice


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Use temporary database path for test isolation."""
    db_file = str(tmp_path / "test_outbound_trigger.db")
    monkeypatch.setenv("BOLBUDDY_DB_PATH", db_file)
    init_db(db_path=db_file)
    return db_file


def test_schedule_outbound_practice_valid():
    """Verify scheduling practice call saves learner preferences and scheduled_calls record."""
    res = schedule_outbound_practice(
        user_id="user_sakshyam_123",
        phone_number="+919876543210",
        scheduled_time="2026-08-11T10:00:00Z",
        name="Sakshyam",
    )

    assert res["success"] is True
    assert res["user_id"] == "user_sakshyam_123"
    assert res["phone_number_masked"] == "+919****10"
    assert res["scheduled_time"] == "2026-08-11T10:00:00Z"
    assert res["status"] == "SCHEDULED"

    # Verify persistent DB record
    user_record = get_user("user_sakshyam_123")
    assert user_record is not None
    assert user_record["name"] == "Sakshyam"
    assert user_record["phone_number"] == "+919876543210"

    calls = get_scheduled_calls("user_sakshyam_123")
    assert len(calls) == 1
    assert calls[0]["status"] == "SCHEDULED"


def test_schedule_outbound_practice_missing_fields():
    """Verify ValueError is raised if required fields are missing."""
    with pytest.raises(ValueError):
        schedule_outbound_practice(
            user_id="", phone_number="+919876543210", scheduled_time="10:00"
        )

    with pytest.raises(ValueError):
        schedule_outbound_practice(
            user_id="user_1", phone_number="", scheduled_time="10:00"
        )


@pytest.mark.asyncio
async def test_trigger_outbound_practice_manual_test_mode(monkeypatch):
    """Verify manual test trigger initiates call handling and safely reports missing credentials."""
    # Pre-populate user record
    schedule_outbound_practice(
        user_id="dev_user_1",
        phone_number="+919876543210",
        scheduled_time="NOW",
        name="TestUser",
    )

    # In unconfigured environment (no LIVEKIT_SIP_TRUNK_ID set), trigger reports PROVIDER_ERROR safely
    monkeypatch.delenv("LIVEKIT_SIP_TRUNK_ID", raising=False)

    res = await trigger_outbound_practice(user_id="dev_user_1")

    assert res["success"] is False
    assert res["status"] == "PROVIDER_ERROR"
    assert res["phone_number_masked"] == "+919****10"
    assert "LIVEKIT_SIP_TRUNK_ID" in res["error"] or "LIVEKIT_SIP_TRUNK_ID" in res.get(
        "missing_config", []
    )
