"""
Unit and evaluation test suite for Day 4 Optional Feature: Forget Me & Data Deletion (forget_my_data).
"""

import os
import tempfile

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant
from db import get_user, init_db
from memory_tools import (
    clear_memory_cache,
    forget_my_data,
    lookup_user_memory,
    save_user_memory,
)


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.fixture
def temp_db():
    """Fixture providing a temporary SQLite database file for isolated testing."""
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
async def test_forget_me_full_lifecycle_flow(temp_db):
    """
    Test 1 & 2 & 3 & 4 & 5 & 6:
    1. Create user memory.
    2. Confirm memory exists in DB and via lookup_user_memory.
    3. Request Forget Me & confirm deletion.
    4. Confirm memory record and in-memory cache are deleted.
    5. Start new call with same user ID.
    6. Verify BolBuddy treats user as having no saved memory.
    """
    user_id = "forget_user_e2e_101"

    # Step 1: Save user memory
    save_res = await save_user_memory(
        context=None,
        name="Vikram",
        learning_goal="job interview",
        user_id=user_id,
    )
    assert save_res == "Memory saved successfully."

    # Step 2: Confirm memory exists
    db_rec = get_user(user_id=user_id, db_path=temp_db)
    assert db_rec is not None
    assert db_rec["name"] == "Vikram"

    lookup_res = await lookup_user_memory(context=None, user_id=user_id)
    assert "Vikram" in lookup_res

    # Step 3: Execute forget_my_data after confirmed consent
    forget_res = await forget_my_data(context=None, user_id=user_id)
    assert forget_res == "Saved memory deleted successfully."

    # Step 4: Verify record is deleted from DB and cache
    assert get_user(user_id=user_id, db_path=temp_db) is None

    # Step 5 & 6: Subsequent call retrieves no saved memory
    new_call_lookup = await lookup_user_memory(context=None, user_id=user_id)
    assert new_call_lookup == "No saved memory found for this user."


@pytest.mark.asyncio
async def test_forget_me_user_declines(temp_db):
    """Test: User declines deletion request -> memory is preserved intact."""
    user_id = "forget_user_declined_102"
    await save_user_memory(
        context=None,
        name="Pooja",
        learning_goal="viva presentation",
        user_id=user_id,
    )

    # User says "No, keep my data" -> forget_my_data is NOT called
    db_rec = get_user(user_id=user_id, db_path=temp_db)
    assert db_rec is not None
    assert db_rec["name"] == "Pooja"

    lookup_res = await lookup_user_memory(context=None, user_id=user_id)
    assert "Pooja" in lookup_res


@pytest.mark.asyncio
async def test_forget_me_repeated_deletion(temp_db):
    """Test: Repeated deletion on already deleted user returns graceful status."""
    user_id = "forget_user_repeat_103"
    await save_user_memory(
        context=None,
        name="Sanjay",
        user_id=user_id,
    )

    # First deletion
    res1 = await forget_my_data(context=None, user_id=user_id)
    assert res1 == "Saved memory deleted successfully."

    # Second deletion on non-existent record
    res2 = await forget_my_data(context=None, user_id=user_id)
    assert (
        res2
        == "No saved memory was found to delete or deletion could not be completed."
    )


@pytest.mark.asyncio
async def test_forget_me_database_failure(temp_db):
    """Test: Database failure during deletion returns error status and does not claim success."""
    os.environ["BOLBUDDY_DB_PATH"] = "/invalid_dir_999/unwritable.db"
    clear_memory_cache()

    user_id = "forget_user_fail_104"
    res = await forget_my_data(context=None, user_id=user_id)

    assert (
        res == "No saved memory was found to delete or deletion could not be completed."
    )
    assert res != "Saved memory deleted successfully."


@pytest.mark.asyncio
async def test_forget_me_agent_confirmation_dialogue() -> None:
    """LLM-as-judge evaluation: Agent MUST ask for confirmation before calling forget_my_data."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="Forget everything you remember about me."
        )

        event_assert = result.expect.next_event()
        try:
            event_assert.is_function_call(name="lookup_user_memory")
            result.expect.next_event().is_function_call_output()
            msg_assert = result.expect.next_event()
        except AssertionError:
            msg_assert = event_assert

        await msg_assert.is_message(role="assistant").judge(
            eval_llm,
            intent="""
            Acknowledges the user's deletion request politely.
            Asks explicitly for verbal confirmation BEFORE deleting any data.
            Does NOT claim to have already deleted data without asking first.
            Does NOT expose internal database jargon or technical details.
            """,
        )

        result.expect.no_more_events()
