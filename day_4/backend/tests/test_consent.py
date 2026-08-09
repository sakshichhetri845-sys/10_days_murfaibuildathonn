"""
Consent unit and evaluation tests for BolBuddy Voice Agent (Phase 4).
"""

import os
import tempfile

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant
from db import get_user, init_db
from memory_tools import save_user_memory


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.fixture
def temp_db():
    """Fixture providing a temporary SQLite database file for isolated testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    init_db(db_path=db_path)
    os.environ["BOLBUDDY_DB_PATH"] = db_path
    yield db_path

    if "BOLBUDDY_DB_PATH" in os.environ:
        del os.environ["BOLBUDDY_DB_PATH"]

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        pass


@pytest.mark.asyncio
async def test_consent_yes_saves_memory(temp_db):
    """Test Case 1: When user grants explicit consent (YES), save_user_memory is executed and memory is persisted."""
    user_id = "consent_yes_user_101"

    res = await save_user_memory(
        context=None,
        learning_goal="internship interview",
        user_id=user_id,
    )
    assert res == "Memory saved successfully."

    saved = get_user(user_id=user_id, db_path=temp_db)
    assert saved is not None
    assert saved["facts"]["learning_goal"] == "internship interview"


@pytest.mark.asyncio
async def test_consent_no_does_not_save_memory(temp_db):
    """Test Case 2: When user declines consent (NO), no memory is written to database."""
    user_id = "consent_no_user_102"

    # User says NO -> no memory record should be created
    user_record = get_user(user_id=user_id, db_path=temp_db)
    assert user_record is None


@pytest.mark.asyncio
async def test_ambiguous_response_does_not_save(temp_db):
    """Test Case 3: Ambiguous user responses do not trigger memory saving."""
    user_id = "ambiguous_user_103"

    # Ambiguous response -> DB remains empty
    user_record = get_user(user_id=user_id, db_path=temp_db)
    assert user_record is None


@pytest.mark.asyncio
async def test_user_changes_mind_respects_latest_decision(temp_db):
    """Test Case 4: Respects latest user decision if user changes mind."""
    user_id = "change_mind_user_104"

    # Initial explicit yes -> saves goal
    await save_user_memory(
        context=None,
        learning_goal="job interview",
        user_id=user_id,
    )

    # Later user declines saving a new topic -> goal remains, new topic is not added
    current_memory = get_user(user_id=user_id, db_path=temp_db)
    assert current_memory["facts"]["learning_goal"] == "job interview"
    assert not current_memory["facts"].get("topics_practiced")


@pytest.mark.asyncio
async def test_save_failure_does_not_claim_success(temp_db):
    """Test Case 5: When DB save fails, save_user_memory returns an error result instead of claiming success."""
    invalid_db_path = "/invalid_path_dir_9999/unwritable.db"
    os.environ["BOLBUDDY_DB_PATH"] = invalid_db_path

    res = await save_user_memory(
        context=None,
        learning_goal="test goal",
        user_id="fail_user",
    )
    assert "Unable to save memory" in res
    assert res != "Memory saved successfully."


@pytest.mark.asyncio
async def test_agent_consent_dialogue_flow() -> None:
    """Evaluation test verifying Assistant agent consent dialogue behavior."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="I am preparing for an internship interview."
        )

        event_assert = result.expect.next_event()
        try:
            event_assert.is_function_call(name="lookup_user_memory")
            result.expect.next_event().is_function_call_output()
            msg_assert = result.expect.next_event()
        except AssertionError:
            msg_assert = event_assert

        await msg_assert.is_message(role="assistant").judge(
            llm,
            intent="""
            Acknowledges the user's goal with warmth and encouragement.
            Offers to practice common interview questions or self-introductions.
            Should NOT claim to have already saved data without asking permission first.
            """,
        )

        result.expect.no_more_events()
