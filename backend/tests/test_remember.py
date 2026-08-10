"""
Unit and evaluation test suite for Memory Inspection feature (what_do_you_remember).
"""

import json
import os
import tempfile

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant
from db import init_db
from memory_tools import (
    clear_memory_cache,
    forget_my_data,
    save_user_memory,
    what_do_you_remember,
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
async def test_remember_new_user(temp_db):
    """Test 1: New user with no saved memory returns friendly empty status."""
    user_id = "rem_new_user_101"
    res = await what_do_you_remember(context=None, user_id=user_id)
    assert res == "No saved memory found for this user."


@pytest.mark.asyncio
async def test_remember_returning_user_fully_populated(temp_db):
    """Test 2: Returning user with full memory returns formatted JSON summary."""
    user_id = "rem_full_user_102"
    await save_user_memory(
        context=None,
        name="Sakshyam",
        language_preference="Hinglish",
        level="intermediate",
        learning_goal="job interview",
        topic_practiced="self introduction",
        recurring_challenge="past tense",
        user_id=user_id,
    )

    res = await what_do_you_remember(context=None, user_id=user_id)
    assert res != "No saved memory found for this user."

    memory_dict = json.loads(res)
    assert memory_dict["name"] == "Sakshyam"
    assert memory_dict["language_preference"] == "Hinglish"
    assert memory_dict["learning_goal"] == "job interview"
    assert "self introduction" in memory_dict["topics_practiced"]
    assert "past tense" in memory_dict["recurring_challenges"]


@pytest.mark.asyncio
async def test_remember_partially_populated_memory(temp_db):
    """Test 3: Partially populated memory returns only available fields without hallucinating missing ones."""
    user_id = "rem_partial_user_103"
    await save_user_memory(
        context=None,
        learning_goal="viva presentation",
        user_id=user_id,
    )

    res = await what_do_you_remember(context=None, user_id=user_id)
    assert res != "No saved memory found for this user."

    memory_dict = json.loads(res)
    assert memory_dict["learning_goal"] == "viva presentation"
    assert "name" not in memory_dict


@pytest.mark.asyncio
async def test_remember_deleted_memory(temp_db):
    """Test 4: Deleted memory returns 'No saved memory found for this user.'."""
    user_id = "rem_deleted_user_104"
    await save_user_memory(
        context=None,
        name="Sunita",
        learning_goal="everyday conversation",
        user_id=user_id,
    )

    # Confirm saved
    pre_res = await what_do_you_remember(context=None, user_id=user_id)
    assert "Sunita" in pre_res

    # Delete memory
    await forget_my_data(context=None, user_id=user_id)

    # Confirm lookup returns empty status
    post_res = await what_do_you_remember(context=None, user_id=user_id)
    assert post_res == "No saved memory found for this user."


@pytest.mark.asyncio
async def test_remember_agent_dialogue_evaluation(temp_db) -> None:
    """LLM-as-judge evaluation: Agent explains memory naturally and offers deletion."""
    user_id = "rem_dialogue_user_105"
    await save_user_memory(
        context=None,
        name="Sakshyam",
        learning_goal="job interview",
        topic_practiced="self introduction",
        user_id=user_id,
    )

    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=f"What do you remember about me? (User ID: {user_id})"
        )

        event_assert = result.expect.next_event()
        try:
            event_assert.is_function_call(name="lookup_user_memory")
            result.expect.next_event().is_function_call_output()
            msg_assert = result.expect.next_event()
        except AssertionError:
            try:
                event_assert.is_function_call(name="what_do_you_remember")
                result.expect.next_event().is_function_call_output()
                msg_assert = result.expect.next_event()
            except AssertionError:
                msg_assert = event_assert

        await msg_assert.is_message(role="assistant").judge(
            eval_llm,
            intent="""
            Explains saved memory naturally and warmly in conversational terms (recalls name Sakshyam and job interview goal).
            Does NOT expose internal database terms, user IDs, or technical JSON keys.
            Warmly offers that the user can request to delete/forget their memory if they wish.
            """,
        )

        result.expect.no_more_events()
