"""
Multilingual and code-mixed memory unit and evaluation tests for HealthSathi.
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
async def test_multilingual_english_memory_saving(temp_db):
    """Test 1: English utterance saves language-neutral memory facts."""
    user_id = "multi_en_user_101"

    res = await save_user_memory(
        context=None,
        name="John",
        language_preference="English",
        reminder_preference="Medication reminder",
        user_id=user_id,
    )
    assert res == "Memory saved successfully."

    saved = get_user(user_id=user_id, db_path=temp_db)
    assert saved["facts"]["reminder_preference"] == "Medication reminder"


@pytest.mark.asyncio
async def test_multilingual_hindi_memory_saving(temp_db):
    """Test 2: Hindi utterance saves language-neutral memory facts."""
    user_id = "multi_hi_user_102"

    res = await save_user_memory(
        context=None,
        name="रमेश",
        language_preference="Hindi",
        reminder_preference="Appointment reminder",
        user_id=user_id,
    )
    assert res == "Memory saved successfully."

    saved = get_user(user_id=user_id, db_path=temp_db)
    assert saved["facts"]["reminder_preference"] == "Appointment reminder"


@pytest.mark.asyncio
async def test_multilingual_hinglish_memory_saving(temp_db):
    """Test 3: Hinglish utterance saves language-neutral memory facts."""
    user_id = "multi_hinglish_user_103"

    res = await save_user_memory(
        context=None,
        name="Sakshyam",
        language_preference="Hinglish",
        reminder_preference="Doctor check-in",
        user_id=user_id,
    )
    assert res == "Memory saved successfully."

    saved = get_user(user_id=user_id, db_path=temp_db)
    assert saved["language_preference"] == "Hinglish"
    assert saved["facts"]["reminder_preference"] == "Doctor check-in"
