"""
Tests for Phase 7 — Conservative Retry Policy & Opt-out Handling.
"""

import pytest

from db import create_scheduled_call, get_scheduled_calls, init_db
from outbound import (
    opt_out_user_from_practice_calls,
    record_call_outcome,
    should_retry_call,
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Use isolated SQLite database for test session."""
    db_file = str(tmp_path / "test_retry.db")
    monkeypatch.setenv("BOLBUDDY_DB_PATH", db_file)
    init_db(db_path=db_file)
    return db_file


def test_declined_call_never_retried(monkeypatch):
    """Verify that explicitly declined calls are never retried."""
    rec = create_scheduled_call(
        user_id="user_declined_retry",
        phone_number="+919876543210",
        scheduled_time="NOW",
    )
    record_call_outcome(rec["id"], "DECLINED")

    updated_call = get_scheduled_calls(user_id="user_declined_retry")[0]
    eligible, reason = should_retry_call(updated_call)

    assert eligible is False
    assert "declined" in reason.lower()


def test_opt_out_cancels_future_calls():
    """Verify saying 'don't call me' cancels future scheduled calls and blocks retries."""
    user_id = "user_optout"
    create_scheduled_call(
        user_id=user_id, phone_number="+919876543210", scheduled_time="NOW"
    )

    opt_res = opt_out_user_from_practice_calls(user_id)
    assert opt_res["success"] is True
    assert opt_res["cancelled_scheduled_calls"] == 1

    calls = get_scheduled_calls(user_id=user_id)
    assert calls[0]["status"] == "CANCELLED"

    eligible, reason = should_retry_call(calls[0])
    assert eligible is False
    assert "opted out" in reason.lower() or "cancelled" in reason.lower()


def test_immediate_retry_blocked_by_delay_window(monkeypatch):
    """Verify immediate retries are blocked when inside the retry delay window."""
    monkeypatch.setenv("OUTBOUND_RETRY_DELAY_SECONDS", "300")
    monkeypatch.setenv("OUTBOUND_MAX_RETRIES", "1")

    rec = create_scheduled_call(
        user_id="user_delay_test",
        phone_number="+919876543210",
        scheduled_time="NOW",
    )
    record_call_outcome(rec["id"], "NO_ANSWER")

    updated_call = get_scheduled_calls(user_id="user_delay_test")[0]
    eligible, reason = should_retry_call(updated_call)

    assert eligible is False
    assert "retry delay window active" in reason.lower()


def test_max_retries_limit_enforced(monkeypatch):
    """Verify maximum retry attempts limit is strictly enforced."""
    monkeypatch.setenv("OUTBOUND_MAX_RETRIES", "1")
    monkeypatch.setenv("OUTBOUND_RETRY_DELAY_SECONDS", "0")

    rec = create_scheduled_call(
        user_id="user_max_retry",
        phone_number="+919876543210",
        scheduled_time="NOW",
    )

    # First attempt: NO_ANSWER
    record_call_outcome(rec["id"], "NO_ANSWER")
    call_attempt1 = get_scheduled_calls(user_id="user_max_retry")[0]

    # Manually simulate incremented attempt count beyond limit
    call_attempt1["attempt_count"] = 2
    eligible, reason = should_retry_call(call_attempt1)

    assert eligible is False
    assert "maximum retry attempts reached" in reason.lower()
