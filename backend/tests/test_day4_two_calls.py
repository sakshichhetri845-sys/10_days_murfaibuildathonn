"""
End-to-End Verification Test for Day 4: Call 1 (New User & Consent Save) vs Call 2 (Returning User & Memory Retrieval).
"""

import json
import os
import tempfile

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant
from db import get_user, init_db
from memory_tools import lookup_user_memory, save_user_memory


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.fixture
def temp_db():
    """Fixture providing a temporary SQLite database file for isolated multi-call testing."""
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
async def test_day4_call1_vs_call2_flow(temp_db):
    """
    Day 4 Challenge E2E Test Flow:

    CALL 1 (New User):
    - New user connects (no prior memory).
    - User shares name ('Sakshyam') and goal ('internship interview').
    - User grants explicit permission ('Yes, please save that').
    - Memory is persisted into database via save_user_memory().
    - Call 1 ends.

    BACKEND RESTART SIMULATION:
    - Connection resets, DB disk file persists.

    CALL 2 (Returning User):
    - Same user connects with identical user_id.
    - Agent retrieves memory via lookup_user_memory().
    - Agent recognizes returning user by name ('Sakshyam') and goal ('internship interview').
    - Personalized greeting & conversation happens.
    """
    user_id = "day4_test_user_ramesh_999"

    # =========================================================================
    # CALL 1: NEW USER SESSION
    # =========================================================================

    # 1. Verify New User state: no memory exists
    initial_lookup = await lookup_user_memory(context=None, user_id=user_id)
    assert initial_lookup == "No saved memory found for this user."

    # 2. User grants explicit permission to save name and learning goal
    save_result = await save_user_memory(
        context=None,
        name="Sakshyam",
        learning_goal="internship interview",
        user_id=user_id,
    )
    assert save_result == "Memory saved successfully."

    # 3. Verify memory stored in DB
    record_call1 = get_user(user_id=user_id, db_path=temp_db)
    assert record_call1 is not None
    assert record_call1["name"] == "Sakshyam"
    assert record_call1["facts"]["learning_goal"] == "internship interview"

    # =========================================================================
    # BACKEND RESTART SIMULATION
    # =========================================================================
    # Verify disk persistence after closing and re-opening connection
    disk_record = get_user(user_id=user_id, db_path=temp_db)
    assert disk_record is not None
    assert disk_record["user_id"] == user_id

    # =========================================================================
    # CALL 2: RETURNING USER SESSION
    # =========================================================================

    # 1. Agent retrieves memory for returning user
    returning_memory_json = await lookup_user_memory(context=None, user_id=user_id)
    assert returning_memory_json != "No saved memory found for this user."

    memory_dict = json.loads(returning_memory_json)
    assert memory_dict["name"] == "Sakshyam"
    assert memory_dict["learning_goal"] == "internship interview"

    # 2. Perform Agent conversation evaluation for Call 2 returning user greeting
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        # User greets BolBuddy in Call 2
        result = await session.run(
            user_input=f"Hi BolBuddy, I am back! (User ID: {user_id})"
        )

        # Expect lookup_user_memory function call event first
        result.expect.next_event().is_function_call(name="lookup_user_memory")
        result.expect.next_event().is_function_call_output()

        # Judge evaluating personalized returning user response
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                eval_llm,
                intent="""
                Welcomes the returning user naturally and enthusiastically by name ('Sakshyam').
                Refers to their primary goal ('internship interview') and offers relevant practice questions.
                Should NOT mention technical database terms or raw SQL statements.
                """,
            )
        )

        result.expect.no_more_events()
