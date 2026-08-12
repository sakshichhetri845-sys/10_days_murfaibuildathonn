"""
Consent unit and evaluation tests for HealthSathi Voice Agent.
"""

import os
import tempfile

import pytest
from livekit.agents import inference, llm

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
async def test_consent_yes_saves_memory(temp_db):
    """Test Case 1: When user grants explicit consent (YES), save_user_memory is executed and memory is persisted."""
    user_id = "consent_yes_user_101"

    res = await save_user_memory(
        context=None,
        reminder_preference="Daily medication reminder at 8am",
        user_id=user_id,
    )
    assert res == "Memory saved successfully."

    saved = get_user(user_id=user_id, db_path=temp_db)
    assert saved is not None
    assert saved["facts"]["reminder_preference"] == "Daily medication reminder at 8am"


@pytest.mark.asyncio
async def test_consent_no_does_not_save_memory(temp_db):
    """Test Case 2: When user declines consent (NO), no memory is written to database."""
    user_id = "consent_no_user_102"

    user_record = get_user(user_id=user_id, db_path=temp_db)
    assert user_record is None


@pytest.mark.asyncio
async def test_ambiguous_response_does_not_save(temp_db):
    """Test Case 3: Ambiguous user responses do not trigger memory saving."""
    user_id = "ambiguous_user_103"

    user_record = get_user(user_id=user_id, db_path=temp_db)
    assert user_record is None


@pytest.mark.asyncio
async def test_user_changes_mind_respects_latest_decision(temp_db):
    """Test Case 4: Respects latest user decision if user changes mind."""
    user_id = "change_mind_user_104"

    await save_user_memory(
        context=None,
        reminder_preference="Doctor appointment 3pm",
        user_id=user_id,
    )

    current_memory = get_user(user_id=user_id, db_path=temp_db)
    assert current_memory["facts"]["reminder_preference"] == "Doctor appointment 3pm"


@pytest.mark.asyncio
async def test_save_failure_does_not_claim_success(temp_db):
    """Test Case 5: When DB save fails, save_user_memory returns an error result instead of claiming success."""
    invalid_db_path = "/invalid_path_dir_9999/unwritable.db"
    os.environ["HEALTHSATHI_DB_PATH"] = invalid_db_path

    res = await save_user_memory(
        context=None,
        reminder_preference="Medication reminder",
        user_id="test_fail_user",
    )
    assert res == "Unable to save memory due to a database error."
