"""
Tests for Phase 6 — Call Outcome Handling.
"""

import pytest

from db import create_scheduled_call, get_scheduled_calls, init_db
from outbound import VALID_CALL_OUTCOMES, record_call_outcome


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Use isolated SQLite database for test session."""
    db_file = str(tmp_path / "test_outcomes.db")
    monkeypatch.setenv("BOLBUDDY_DB_PATH", db_file)
    init_db(db_path=db_file)
    return db_file


def test_valid_outcomes_set():
    """Verify all 7 mandatory Phase 6 outcomes exist in valid outcomes set."""
    mandatory = {
        "COMPLETED",
        "DECLINED",
        "BUSY",
        "NO_ANSWER",
        "VOICEMAIL",
        "IMMEDIATE_HANGUP",
        "PROVIDER_ERROR",
    }
    assert mandatory.issubset(VALID_CALL_OUTCOMES)


@pytest.mark.parametrize(
    "outcome",
    [
        "COMPLETED",
        "DECLINED",
        "BUSY",
        "NO_ANSWER",
        "VOICEMAIL",
        "IMMEDIATE_HANGUP",
        "PROVIDER_ERROR",
    ],
)
def test_record_each_call_outcome(outcome):
    """Test recording and storing each explicit call outcome in database."""
    # Pre-create scheduled call record
    rec = create_scheduled_call(
        user_id="user_outcome_test",
        phone_number="+919876543210",
        scheduled_time="NOW",
    )
    call_id = rec["id"]

    res = record_call_outcome(
        call_id=call_id,
        outcome=outcome,
        user_id="user_outcome_test",
        details=f"Test details for {outcome}",
    )

    assert res["success"] is True
    assert res["outcome"] == outcome

    # Verify DB persistence
    calls = get_scheduled_calls(user_id="user_outcome_test")
    assert len(calls) > 0
    assert calls[0]["status"] == outcome


def test_invalid_outcome_fallback():
    """Verify unrecognized outcomes fall back safely to PROVIDER_ERROR without crashing."""
    rec = create_scheduled_call(
        user_id="user_fallback",
        phone_number="+919876543210",
        scheduled_time="NOW",
    )
    res = record_call_outcome(call_id=rec["id"], outcome="UNKNOWN_FAILURE_STATE")

    assert res["outcome"] == "PROVIDER_ERROR"
