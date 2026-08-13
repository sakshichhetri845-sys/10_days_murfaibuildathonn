"""
Unit tests for Phase 2 Schedule Model Persistence API.
"""

import pytest

from schedule_model import (
    calculate_next_call_at,
    cancel_schedule,
    create_or_update_schedule,
    get_schedule,
    parse_time_str,
    validate_phone_number,
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Isolated database environment for schedule tests."""
    db_file = str(tmp_path / "test_schedule.db")
    monkeypatch.setenv("BOLBUDDY_DB_PATH", db_file)
    return db_file


def test_time_parsing_and_validation():
    """Verify time string parsing formats and invalid value rejection."""
    assert parse_time_str("20:00") == (20, 0)
    assert parse_time_str("8:30 PM") == (20, 30)
    assert parse_time_str("08:00 AM") == (8, 0)
    assert parse_time_str("12:00 PM") == (12, 0)
    assert parse_time_str("12:00 AM") == (0, 0)

    with pytest.raises(ValueError):
        parse_time_str("invalid_time")
    with pytest.raises(ValueError):
        parse_time_str("25:00")


def test_phone_number_validation():
    """Verify phone number format validation."""
    assert validate_phone_number("+919876543210") == "+919876543210"
    assert validate_phone_number(" 9876543210 ") == "9876543210"

    with pytest.raises(ValueError):
        validate_phone_number("123")
    with pytest.raises(ValueError):
        validate_phone_number("")


def test_create_and_get_schedule(setup_test_db):
    """Test CREATE schedule and GET schedule."""
    user_id = "user_sched_01"
    sched = create_or_update_schedule(
        user_id=user_id,
        phone_number="+919876543210",
        practice_topic="Job Interview English",
        preferred_time="20:00",
        timezone="Asia/Kolkata",
        db_path=setup_test_db,
    )

    assert sched["user_id"] == user_id
    assert sched["phone_number"] == "+919876543210"
    assert sched["practice_topic"] == "Job Interview English"
    assert sched["preferred_time"] == "20:00"
    assert sched["timezone"] == "Asia/Kolkata"
    assert sched["enabled"] is True
    assert sched["next_call_at"] is not None

    fetched = get_schedule(user_id, db_path=setup_test_db)
    assert fetched == sched


def test_update_schedule(setup_test_db):
    """Test UPDATE existing schedule."""
    user_id = "user_sched_02"
    create_or_update_schedule(
        user_id=user_id,
        phone_number="+919876543210",
        practice_topic="Small Talk",
        preferred_time="19:00",
        timezone="America/New_York",
        db_path=setup_test_db,
    )

    updated = create_or_update_schedule(
        user_id=user_id,
        phone_number="+919876543210",
        practice_topic="Advanced Viva Prep",
        preferred_time="21:30",
        timezone="America/New_York",
        db_path=setup_test_db,
    )

    assert updated["practice_topic"] == "Advanced Viva Prep"
    assert updated["preferred_time"] == "21:30"
    assert updated["timezone"] == "America/New_York"


def test_cancel_schedule(setup_test_db):
    """Test CANCEL schedule."""
    user_id = "user_sched_03"
    create_or_update_schedule(
        user_id=user_id,
        phone_number="+919876543210",
        practice_topic="General English",
        preferred_time="20:00",
        db_path=setup_test_db,
    )

    success = cancel_schedule(user_id, db_path=setup_test_db)
    assert success is True

    sched = get_schedule(user_id, db_path=setup_test_db)
    assert sched["enabled"] is False


def test_timezone_user_support():
    """Verify schedule supports user-provided timezones accurately."""
    iso_kolkata = calculate_next_call_at("20:00", "Asia/Kolkata")
    calculate_next_call_at("20:00", "Asia/Kathmandu")
    iso_ny = calculate_next_call_at("20:00", "America/New_York")

    assert iso_kolkata != iso_ny
    assert iso_kolkata is not None
