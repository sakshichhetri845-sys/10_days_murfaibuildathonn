"""
Tests for Day 8 — HealthSathi Call Analytics Dashboard & Outcome Tracking.
"""

import pytest
from db import get_call_analytics, init_db, save_call_analytics


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Use an isolated SQLite database for test session."""
    db_file = str(tmp_path / "test_healthsathi_analytics.db")
    monkeypatch.setenv("HEALTHSATHI_DB_PATH", db_file)
    monkeypatch.setenv("BOLBUDDY_DB_PATH", db_file)
    init_db(db_path=db_file)
    return db_file


def test_1_successful_general_guidance_call():
    """Verify recording a successful GENERAL_GUIDANCE call."""
    res = save_call_analytics(
        session_id="session_guidance_01",
        duration=45,
        channel="browser",
        outcome="successful",
        outcome_type="GENERAL_GUIDANCE",
    )
    assert res["outcome"] == "successful"
    assert res["outcome_type"] == "GENERAL_GUIDANCE"

    analytics = get_call_analytics(range_filter="all")
    assert analytics["total_calls"] == 1
    assert analytics["successful_calls"] == 1
    assert analytics["outcome_breakdown"]["GENERAL_GUIDANCE"] == 1


def test_2_successful_triage_call():
    """Verify recording a successful TRIAGE_COMPLETED call."""
    res = save_call_analytics(
        session_id="session_triage_02",
        duration=60,
        channel="browser",
        outcome="successful",
        outcome_type="TRIAGE_COMPLETED",
    )
    assert res["outcome"] == "successful"
    assert res["outcome_type"] == "TRIAGE_COMPLETED"

    analytics = get_call_analytics(range_filter="all")
    assert analytics["outcome_breakdown"]["TRIAGE_COMPLETED"] == 1


def test_3_successful_facility_lookup_call():
    """Verify recording a successful FACILITY_FOUND call."""
    res = save_call_analytics(
        session_id="session_facility_03",
        duration=50,
        channel="SIP",
        outcome="successful",
        outcome_type="FACILITY_FOUND",
    )
    assert res["outcome"] == "successful"
    assert res["outcome_type"] == "FACILITY_FOUND"
    assert res["channel"] == "SIP"

    analytics = get_call_analytics(range_filter="all")
    assert analytics["outcome_breakdown"]["FACILITY_FOUND"] == 1


def test_4_successful_human_escalation_call():
    """Verify recording a successful HUMAN_ESCALATION call."""
    res = save_call_analytics(
        session_id="session_escalation_04",
        duration=90,
        channel="browser",
        outcome="successful",
        outcome_type="HUMAN_ESCALATION",
    )
    assert res["outcome"] == "successful"
    assert res["outcome_type"] == "HUMAN_ESCALATION"

    analytics = get_call_analytics(range_filter="all")
    assert analytics["outcome_breakdown"]["HUMAN_ESCALATION"] == 1


def test_5_failed_incomplete_and_technical_error_calls():
    """Verify recording failed INCOMPLETE and TECHNICAL_ERROR calls."""
    res1 = save_call_analytics(
        session_id="session_incomplete_05",
        duration=12,
        channel="browser",
        outcome="failed",
        outcome_type="INCOMPLETE",
    )
    assert res1["outcome"] == "failed"
    assert res1["outcome_type"] == "INCOMPLETE"

    res2 = save_call_analytics(
        session_id="session_error_06",
        duration=5,
        channel="SIP",
        outcome="failed",
        outcome_type="TECHNICAL_ERROR",
    )
    assert res2["outcome"] == "failed"
    assert res2["outcome_type"] == "TECHNICAL_ERROR"

    analytics = get_call_analytics(range_filter="all")
    assert analytics["failed_calls"] == 2
    assert analytics["outcome_breakdown"]["INCOMPLETE"] == 1
    assert analytics["outcome_breakdown"]["TECHNICAL_ERROR"] == 1


def test_6_analytics_totals():
    """Verify total call counts across mixed outcomes."""
    save_call_analytics(
        session_id="s1", duration=30, outcome="successful", outcome_type="GENERAL_GUIDANCE"
    )
    save_call_analytics(
        session_id="s2", duration=40, outcome="successful", outcome_type="TRIAGE_COMPLETED"
    )
    save_call_analytics(
        session_id="s3", duration=15, outcome="failed", outcome_type="INCOMPLETE"
    )

    analytics = get_call_analytics(range_filter="all")
    assert analytics["total_calls"] == 3
    assert analytics["successful_calls"] == 2
    assert analytics["failed_calls"] == 1


def test_7_success_rate():
    """Verify success rate math: successful / total * 100 with zero handling."""
    # 0 calls -> 0.0%
    analytics = get_call_analytics(range_filter="all")
    assert analytics["success_rate"] == 0.0

    # 3 successful out of 4 calls -> 75.0%
    save_call_analytics(session_id="c1", outcome="successful", outcome_type="GENERAL_GUIDANCE")
    save_call_analytics(session_id="c2", outcome="successful", outcome_type="TRIAGE_COMPLETED")
    save_call_analytics(session_id="c3", outcome="successful", outcome_type="FACILITY_FOUND")
    save_call_analytics(session_id="c4", outcome="failed", outcome_type="INCOMPLETE")

    analytics = get_call_analytics(range_filter="all")
    assert analytics["total_calls"] == 4
    assert analytics["successful_calls"] == 3
    assert analytics["failed_calls"] == 1
    assert analytics["success_rate"] == 75.0


def test_8_outcome_breakdown():
    """Verify outcome breakdown dictionary counts."""
    save_call_analytics(session_id="b1", outcome="successful", outcome_type="GENERAL_GUIDANCE")
    save_call_analytics(session_id="b2", outcome="successful", outcome_type="GENERAL_GUIDANCE")
    save_call_analytics(session_id="b3", outcome="successful", outcome_type="TRIAGE_COMPLETED")
    save_call_analytics(session_id="b4", outcome="successful", outcome_type="FACILITY_FOUND")
    save_call_analytics(session_id="b5", outcome="successful", outcome_type="HUMAN_ESCALATION")
    save_call_analytics(session_id="b6", outcome="failed", outcome_type="INCOMPLETE")

    analytics = get_call_analytics(range_filter="all")
    bd = analytics["outcome_breakdown"]
    assert bd["GENERAL_GUIDANCE"] == 2
    assert bd["TRIAGE_COMPLETED"] == 1
    assert bd["FACILITY_FOUND"] == 1
    assert bd["HUMAN_ESCALATION"] == 1
    assert bd["INCOMPLETE"] == 1
    assert bd["TECHNICAL_ERROR"] == 0


def test_9_recent_calls():
    """Verify recent calls list formatting and fields."""
    save_call_analytics(
        session_id="rec_1",
        duration=25,
        channel="browser",
        outcome="successful",
        outcome_type="TRIAGE_COMPLETED",
    )
    save_call_analytics(
        session_id="rec_2",
        duration=65,
        channel="SIP",
        outcome="successful",
        outcome_type="HUMAN_ESCALATION",
    )

    analytics = get_call_analytics(range_filter="all")
    recent = analytics["recent_calls"]
    assert len(recent) == 2

    # Check allowed fields in recent call record
    for item in recent:
        assert "id" in item
        assert "timestamp" in item
        assert "duration" in item
        assert "channel" in item
        assert "outcome" in item
        assert "outcome_type" in item


def test_10_no_sensitive_medical_info_in_analytics():
    """Verify no sensitive medical information, symptoms, or diagnoses exist in analytics data."""
    save_call_analytics(
        session_id="privacy_test_01",
        duration=50,
        channel="browser",
        outcome="successful",
        outcome_type="TRIAGE_COMPLETED",
    )

    analytics = get_call_analytics(range_filter="all")
    record = analytics["recent_calls"][0]

    sensitive_keys = {
        "symptoms",
        "diagnosis",
        "medication",
        "medical_history",
        "transcript",
        "phone_number",
        "password",
        "otp",
        "pin",
    }
    for key in sensitive_keys:
        assert key not in record, f"Sensitive field '{key}' was exposed in analytics!"
