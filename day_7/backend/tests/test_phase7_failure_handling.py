"""
Unit tests for Phase 7 Failure Handling.
"""

import pytest

from db import create_scheduled_call, get_scheduled_calls
from outbound import record_call_outcome, should_retry_call, trigger_outbound_practice


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Isolated database environment for Phase 7 failure handling tests."""
    db_file = str(tmp_path / "test_phase7.db")
    monkeypatch.setenv("BOLBUDDY_DB_PATH", db_file)
    monkeypatch.delenv("LIVEKIT_SIP_TRUNK_ID", raising=False)
    monkeypatch.delenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID", raising=False)
    from db import init_db

    init_db(db_file)
    return db_file


@pytest.mark.asyncio
async def test_uninitiated_call_failure_handling(setup_test_db):
    """Verify failed initiation logs PROVIDER_ERROR and returns safe message."""
    res = await trigger_outbound_practice(
        user_id="user_uninit_fail",
        phone_number="+919876543210",
        db_path=setup_test_db,
    )

    assert res["success"] is False
    assert res["status"] == "PROVIDER_ERROR"
    assert "LIVEKIT_SIP_TRUNK_ID" in res["error"]


def test_no_answer_recording_and_retry_block(setup_test_db):
    """Verify NO_ANSWER outcome is recorded and not repeatedly called."""
    record = create_scheduled_call("user_no_ans", "+919876543210", "20:00")
    call_id = record["id"]

    res = record_call_outcome(call_id, "NO_ANSWER", user_id="user_no_ans")
    assert res["outcome"] == "NO_ANSWER"

    calls = get_scheduled_calls("user_no_ans")
    call_rec = calls[0]
    call_rec["attempt_count"] = 5  # Exceed max retries

    should_retry, reason = should_retry_call(call_rec)
    assert should_retry is False
    assert "Maximum retry attempts reached" in reason


def test_immediate_hangup_call_ended_recording(setup_test_db):
    """Verify learner hangup is recorded as CALL_ENDED."""
    record = create_scheduled_call("user_hangup", "+919876543210", "20:00")
    call_id = record["id"]

    res = record_call_outcome(call_id, "CALL_ENDED", user_id="user_hangup")
    assert res["outcome"] == "CALL_ENDED"

    calls = get_scheduled_calls("user_hangup")
    assert calls[0]["status"] == "CALL_ENDED"
