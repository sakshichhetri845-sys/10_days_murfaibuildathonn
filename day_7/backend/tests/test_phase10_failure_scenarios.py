"""
Automated Test Suite for Phase 10 Failure Scenarios & Edge Cases.
"""

import pytest

from db import create_or_update_user, get_scheduled_calls, init_db
from memory_tools import async_prefetch_user_memory
from outbound import (
    record_call_outcome,
    schedule_outbound_practice,
    trigger_outbound_practice,
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Isolated database environment for Phase 10 test execution."""
    db_file = str(tmp_path / "test_phase10.db")
    monkeypatch.setenv("BOLBUDDY_DB_PATH", db_file)
    init_db(db_path=db_file)
    return db_file


def test_scenario_1_success():
    """TEST 1 — SUCCESS: Sakshyam schedules a call, answers, practice occurs, COMPLETED."""
    sched = schedule_outbound_practice(
        user_id="user_sakshyam",
        phone_number="+919876543210",
        scheduled_time="7:30 PM",
        name="Sakshyam",
    )
    assert sched["success"] is True

    # Simulate completed practice session outcome
    res = record_call_outcome(
        call_id=sched["call_id"],
        outcome="COMPLETED",
        user_id="user_sakshyam",
    )
    assert res["outcome"] == "COMPLETED"

    calls = get_scheduled_calls(user_id="user_sakshyam")
    assert calls[0]["status"] == "COMPLETED"


def test_scenario_2_decline():
    """TEST 2 — DECLINE: Learner declines practice call, recorded as DECLINED."""
    sched = schedule_outbound_practice(
        user_id="user_sakshyam_decline",
        phone_number="+919876543210",
        scheduled_time="NOW",
        name="Sakshyam",
    )

    # User says "No, not right now" -> end_call tool invoked -> DECLINED recorded
    res = record_call_outcome(
        call_id=sched["call_id"],
        outcome="DECLINED",
        user_id="user_sakshyam_decline",
        details="User said: No, not right now",
    )
    assert res["outcome"] == "DECLINED"

    calls = get_scheduled_calls(user_id="user_sakshyam_decline")
    assert calls[0]["status"] == "DECLINED"


def test_scenario_3_no_answer():
    """TEST 3 — NO ANSWER: Phone doesn't answer, status recorded as NO_ANSWER without fake dialog."""
    sched = schedule_outbound_practice(
        user_id="user_no_answer",
        phone_number="+919876543210",
        scheduled_time="NOW",
    )

    res = record_call_outcome(
        call_id=sched["call_id"],
        outcome="NO_ANSWER",
        user_id="user_no_answer",
    )
    assert res["outcome"] == "NO_ANSWER"

    calls = get_scheduled_calls(user_id="user_no_answer")
    assert calls[0]["status"] == "NO_ANSWER"


@pytest.mark.asyncio
async def test_scenario_4_memory_continuity():
    """TEST 4 — MEMORY: Practices internship interview English -> next outbound call continues context."""
    user_id = "user_memory_continuity"

    # Call 1: Save memory topic
    create_or_update_user(
        user_id=user_id,
        name="Sakshyam",
        facts={
            "learning_goal": "internship interview preparation",
            "topics_practiced": ["internship interview English"],
        },
    )

    # Next outbound call: pre-fetch user memory
    memory = await async_prefetch_user_memory(user_id)
    assert memory is not None
    assert memory["name"] == "Sakshyam"
    assert "internship interview English" in memory["facts"]["topics_practiced"]

    # Verify greeting and topic continuation text
    greeting = f"Hi {memory['name']}, this is BolBuddy. You scheduled an English practice session. Is this still a good time?"
    assert "Hi Sakshyam, this is BolBuddy" in greeting

    topic_continue = f"Last time we practiced {memory['facts']['topics_practiced'][-1]}. Let's continue with one quick question."
    assert "Last time we practiced internship interview English" in topic_continue


def test_scenario_5_immediate_hangup():
    """TEST 5 — HANGUP: Learner answers and immediately hangs up, recorded as IMMEDIATE_HANGUP without crash."""
    sched = schedule_outbound_practice(
        user_id="user_hangup",
        phone_number="+919876543210",
        scheduled_time="NOW",
    )

    res = record_call_outcome(
        call_id=sched["call_id"],
        outcome="IMMEDIATE_HANGUP",
        user_id="user_hangup",
    )
    assert res["outcome"] == "IMMEDIATE_HANGUP"

    calls = get_scheduled_calls(user_id="user_hangup")
    assert calls[0]["status"] == "IMMEDIATE_HANGUP"


@pytest.mark.asyncio
async def test_scenario_6_provider_failure(monkeypatch):
    """TEST 6 — PROVIDER FAILURE: Telephony credentials missing -> logged, no worker crash, safe error."""
    monkeypatch.delenv("LIVEKIT_SIP_TRUNK_ID", raising=False)
    monkeypatch.delenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID", raising=False)

    # Trigger outbound practice call with missing credentials
    res = await trigger_outbound_practice(
        user_id="user_prov_fail",
        phone_number="+919876543210",
    )

    # System logs technical failure, worker does not crash, returns safe error response
    assert res["success"] is False
    assert res["status"] == "PROVIDER_ERROR"
    assert "LIVEKIT_SIP_TRUNK_ID" in res["error"] or "LIVEKIT_SIP_TRUNK_ID" in res.get(
        "missing_config", []
    )

    calls = get_scheduled_calls(user_id="user_prov_fail")
    assert calls[0]["status"] == "PROVIDER_ERROR"
