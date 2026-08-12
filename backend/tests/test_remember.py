"""
Unit and evaluation test suite for Memory Inspection feature (what_do_you_remember) for HealthSathi.
"""

import json
import os
import tempfile

import pytest
from livekit.agents import inference, llm

from db import init_db
from memory_tools import (
    clear_memory_cache,
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
    os.environ["HEALTHSATHI_DB_PATH"] = db_path
    clear_memory_cache()

    yield db_path

    clear_memory_cache()
    if "HEALTHSATHI_DB_PATH" in os.environ:
        del os.environ["HEALTHSATHI_DB_PATH"]

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
        reminder_preference="Morning medication 9am",
        contact_preference="phone",
        user_id=user_id,
    )

    res = await what_do_you_remember(context=None, user_id=user_id)
    assert res != "No saved memory found for this user."

    memory_dict = json.loads(res)
    assert memory_dict["name"] == "Sakshyam"
    assert memory_dict["language_preference"] == "Hinglish"
    assert memory_dict["reminder_preference"] == "Morning medication 9am"
    assert memory_dict["contact_preference"] == "phone"


@pytest.mark.asyncio
async def test_remember_partially_populated_memory(temp_db):
    """Test 3: Partially populated memory returns only available fields without hallucinating missing ones."""
    user_id = "rem_partial_user_103"
    await save_user_memory(
        context=None,
        reminder_preference="Doctor appointment 3pm",
        user_id=user_id,
    )

    res = await what_do_you_remember(context=None, user_id=user_id)
    assert res != "No saved memory found for this user."

    memory_dict = json.loads(res)
    assert memory_dict["reminder_preference"] == "Doctor appointment 3pm"
    assert "name" not in memory_dict
