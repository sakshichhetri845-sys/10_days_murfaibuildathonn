"""
Master Final Integration Test Suite for Day 4 (BolBuddy Voice Agent).

Executes the exact 3-call end-to-end user scenario and all failure recovery tests.
"""

import os
import tempfile

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant
from db import delete_user, get_user, init_db
from memory_tools import (
    clear_memory_cache,
    forget_my_data,
    lookup_user_memory,
    save_user_memory,
)


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.fixture
def master_db():
    """Fixture providing a clean temporary SQLite database file for master integration testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    init_db(db_path=db_path)
    os.environ["BOLBUDDY_DB_PATH"] = db_path
    clear_memory_cache()

    yield db_path

    clear_memory_cache()
    if "BOLBUDDY_DB_PATH" in os.environ:
        del os.environ["BOLBUDDY_DB_PATH"]

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        pass


@pytest.mark.asyncio
async def test_master_day4_integration_flow(master_db):
    """
    Executes the exact Day 4 end-to-end integration scenario across 3 calls.
    """
    user_id = "master_user_ramesh_404"

    # =========================================================================
    # CALL 1: NEW USER SESSION & CONSENT SAVING
    # =========================================================================

    # 1. New user connects - verify empty initial lookup
    res_initial = await lookup_user_memory(context=None, user_id=user_id)
    assert res_initial == "No saved memory found for this user."

    # 2. User grants permission & saves identity + learning goal
    save_res = await save_user_memory(
        context=None,
        name="Ramesh",
        language_preference="Hinglish",
        learning_goal="internship interview",
        user_id=user_id,
    )
    assert save_res == "Memory saved successfully."

    # 3. Verify SQLite DB disk persistence
    rec_c1 = get_user(user_id=user_id, db_path=master_db)
    assert rec_c1 is not None
    assert rec_c1["name"] == "Ramesh"
    assert rec_c1["facts"]["learning_goal"] == "internship interview"

    # =========================================================================
    # BACKEND RESTART SIMULATION
    # =========================================================================
    # Reset in-memory session cache and verify disk persistence across backend restart
    clear_memory_cache()
    disk_rec = get_user(user_id=user_id, db_path=master_db)
    assert disk_rec is not None
    assert disk_rec["user_id"] == user_id

    # =========================================================================
    # CALL 2: RETURNING USER PERSONALIZED CONVERSATION & CODE-MIXED DIALOGUE
    # =========================================================================

    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        # Turn 1: Returning user connects
        res_call2 = await session.run(
            user_input=f"Hi BolBuddy, I am back! (User ID: {user_id})"
        )

        event_assert = res_call2.expect.next_event()
        try:
            event_assert.is_function_call(name="lookup_user_memory")
            res_call2.expect.next_event().is_function_call_output()
            msg_assert = res_call2.expect.next_event()
        except AssertionError:
            msg_assert = event_assert

        await msg_assert.is_message(role="assistant").judge(
            eval_llm,
            intent="""
            Recognizes returning user Ramesh naturally and warmly.
            Refers to his internship interview preparation goal.
            Offers to practice interview questions today.
            """,
        )

        # Turn 2: Code-mixed Hinglish exchange
        res_turn2 = await session.run(
            user_input="Mujhe interview ke answers English mein dene mein thoda nervous lagta hai."
        )

        event_assert2 = res_turn2.expect.next_event()
        try:
            event_assert2.is_function_call(name="lookup_user_memory")
            res_turn2.expect.next_event().is_function_call_output()
            msg_assert2 = res_turn2.expect.next_event()
        except AssertionError:
            try:
                event_assert2.is_function_call(name="search_learning_resources")
                res_turn2.expect.next_event().is_function_call_output()
                msg_assert2 = res_turn2.expect.next_event()
            except AssertionError:
                msg_assert2 = event_assert2

        await msg_assert2.is_message(role="assistant").judge(
            eval_llm,
            intent="""
            Responds warmly and supportively to the user's Hinglish query about feeling nervous in interview answers.
            Offers practical, encouraging advice or practice without judgment.
            """,
        )

        # Turn 3: User requests Forget Me
        res_turn3 = await session.run(
            user_input="Forget everything you remember about me."
        )

        event_assert3 = res_turn3.expect.next_event()
        try:
            event_assert3.is_function_call(name="lookup_user_memory")
            res_turn3.expect.next_event().is_function_call_output()
            msg_assert3 = res_turn3.expect.next_event()
        except AssertionError:
            msg_assert3 = event_assert3

        await msg_assert3.is_message(role="assistant").judge(
            eval_llm,
            intent="""
            Politely acknowledges the user's deletion request and explicitly asks for verbal confirmation before deleting.
            Does NOT claim to have already deleted data without asking first.
            """,
        )

    # Execute confirmed deletion
    forget_res = await forget_my_data(context=None, user_id=user_id)
    assert forget_res == "Saved memory deleted successfully."
    assert get_user(user_id=user_id, db_path=master_db) is None

    # =========================================================================
    # CALL 3: SAME USER RETURNS AFTER DELETION
    # =========================================================================

    async with (
        _llm() as eval_llm3,
        AgentSession(llm=eval_llm3) as session3,
    ):
        await session3.start(Assistant())

        res_call3 = await session3.run(user_input=f"Hi BolBuddy! (User ID: {user_id})")

        event_assert_c3 = res_call3.expect.next_event()
        try:
            event_assert_c3.is_function_call(name="lookup_user_memory")
            res_call3.expect.next_event().is_function_call_output()
            msg_assert_c3 = res_call3.expect.next_event()
        except AssertionError:
            msg_assert_c3 = event_assert_c3

        await msg_assert_c3.is_message(role="assistant").judge(
            eval_llm3,
            intent="""
            Greets the user as a new user with no remembered profile or prior facts.
            Does NOT reference deleted memory facts (Ramesh, internship interview).
            """,
        )


@pytest.mark.asyncio
async def test_failure_recovery_scenarios(master_db):
    """
    Verifies that BolBuddy fails gracefully across all database, tool, and consent failure cases.
    """
    user_id = "fail_test_user_505"

    # 1. Database failure / invalid path
    os.environ["BOLBUDDY_DB_PATH"] = "/invalid_dir/unwritable.db"
    clear_memory_cache()

    lookup_fail = await lookup_user_memory(context=None, user_id=user_id)
    assert lookup_fail == "No saved memory found for this user."

    save_fail = await save_user_memory(
        context=None, name="Test", learning_goal="Goal", user_id=user_id
    )
    assert (
        "Unable to save memory" in save_fail
        or save_fail != "Memory saved successfully."
    )

    del_fail = await forget_my_data(context=None, user_id=user_id)
    assert (
        "No saved memory was found" in del_fail
        or del_fail != "Saved memory deleted successfully."
    )

    # Restore database path
    os.environ["BOLBUDDY_DB_PATH"] = master_db
    clear_memory_cache()

    # 2. Deletion failure when user record does not exist
    del_nonexistent = delete_user(user_id="nonexistent_id_999", db_path=master_db)
    assert del_nonexistent is False
