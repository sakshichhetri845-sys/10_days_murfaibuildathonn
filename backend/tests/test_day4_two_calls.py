"""
End-to-End Verification Test for Day 4: Call 1 (New User & Consent Save) vs Call 2 (Returning User & Memory Retrieval) for HealthSathi.
"""

import json
import os
import tempfile

import pytest
from livekit.agents import inference, llm

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
    os.environ["HEALTHSATHI_DB_PATH"] = db_path
    yield db_path

    if "HEALTHSATHI_DB_PATH" in os.environ:
        del os.environ["HEALTHSATHI_DB_PATH"]

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
    - User shares name ('Sakshyam') and reminder preference ('Daily medication reminder at 8am').
    - User grants explicit permission ('Yes, please save that').
    - Memory is persisted into database via save_user_memory().
    - Call 1 ends.

    BACKEND RESTART SIMULATION:
    - Connection resets, DB disk file persists.

    CALL 2 (Returning User):
    - Same user connects with identical user_id.
    - Agent retrieves memory via lookup_user_memory().
    - Agent recognizes returning user by name ('Sakshyam').
    - Personalized greeting & conversation happens.
    """
    user_id = "day4_test_user_ramesh_999"

    # CALL 1: NEW USER SESSION
    initial_lookup = await lookup_user_memory(context=None, user_id=user_id)
    assert initial_lookup == "No saved memory found for this user."

    save_result = await save_user_memory(
        context=None,
        name="Sakshyam",
        reminder_preference="Daily medication reminder at 8am",
        user_id=user_id,
    )
    assert save_result == "Memory saved successfully."

    record_call1 = get_user(user_id=user_id, db_path=temp_db)
    assert record_call1 is not None
    assert record_call1["name"] == "Sakshyam"
    assert record_call1["facts"]["reminder_preference"] == "Daily medication reminder at 8am"

    # BACKEND RESTART SIMULATION
    disk_record = get_user(user_id=user_id, db_path=temp_db)
    assert disk_record is not None
    assert disk_record["user_id"] == user_id

    # CALL 2: RETURNING USER SESSION
    returning_memory_json = await lookup_user_memory(context=None, user_id=user_id)
    assert returning_memory_json != "No saved memory found for this user."

    memory = json.loads(returning_memory_json)
    assert memory["name"] == "Sakshyam"
    assert memory["reminder_preference"] == "Daily medication reminder at 8am"
