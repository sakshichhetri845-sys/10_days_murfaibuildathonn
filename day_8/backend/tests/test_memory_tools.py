"""
Unit tests for HealthSathi memory tools (src/memory_tools.py).
"""

import json
import os
import tempfile

import pytest

from db import create_or_update_user, init_db
from memory_tools import lookup_user_memory, save_user_memory


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
async def test_lookup_existing_user(temp_db):
    """Test lookup_user_memory for an existing user with saved health facts."""
    user_id = "user_ramesh_test_1"
    create_or_update_user(
        user_id=user_id,
        name="Sakshyam",
        language_preference="English + Hindi",
        facts={
            "reminder_preference": "Morning medication",
            "contact_preference": "phone",
        },
        db_path=temp_db,
    )

    result_json = await lookup_user_memory(context=None, user_id=user_id)
    assert result_json != "No saved memory found for this user."

    memory = json.loads(result_json)
    assert memory["name"] == "Sakshyam"
    assert memory["language_preference"] == "English + Hindi"
    assert memory["reminder_preference"] == "Morning medication"
    assert memory["contact_preference"] == "phone"


@pytest.mark.asyncio
async def test_lookup_new_user(temp_db):
    """Test lookup_user_memory for a new user with no saved record."""
    result = await lookup_user_memory(context=None, user_id="new_unknown_user_999")
    assert result == "No saved memory found for this user."


@pytest.mark.asyncio
async def test_save_user(temp_db):
    """Test save_user_memory creates a new user profile with health memory."""
    user_id = "user_save_test_2"

    res = await save_user_memory(
        context=None,
        name="Priya",
        language_preference="Hinglish",
        reminder_preference="Weekly appointment check-in",
        contact_preference="phone",
        user_id=user_id,
    )

    assert res == "Memory saved successfully."

    lookup_res = await lookup_user_memory(context=None, user_id=user_id)
    memory = json.loads(lookup_res)

    assert memory["name"] == "Priya"
    assert memory["language_preference"] == "Hinglish"
    assert memory["reminder_preference"] == "Weekly appointment check-in"
    assert memory["contact_preference"] == "phone"


@pytest.mark.asyncio
async def test_update_user(temp_db):
    """Test save_user_memory updates an existing user profile."""
    user_id = "user_update_test_3"

    # Initial save
    await save_user_memory(
        context=None,
        name="Kavita",
        reminder_preference="Medication reminder",
        user_id=user_id,
    )

    # Subsequent update
    await save_user_memory(
        context=None,
        contact_preference="voice assistant",
        user_id=user_id,
    )

    lookup_res = await lookup_user_memory(context=None, user_id=user_id)
    memory = json.loads(lookup_res)

    assert memory["name"] == "Kavita"
    assert memory["reminder_preference"] == "Medication reminder"
    assert memory["contact_preference"] == "voice assistant"


@pytest.mark.asyncio
async def test_missing_fields(temp_db):
    """Test save_user_memory when no memory fields are passed."""
    user_id = "user_empty_fields_4"

    res = await save_user_memory(context=None, user_id=user_id)
    assert res == "No memory fields were provided to save."


@pytest.mark.asyncio
async def test_database_failure(temp_db):
    """Test lookup and save when database path is invalid or unwritable."""
    invalid_db_path = "/invalid_directory_path_12345/unwritable.db"
    os.environ["HEALTHSATHI_DB_PATH"] = invalid_db_path

    lookup_res = await lookup_user_memory(context=None, user_id="test_user")
    assert lookup_res == "No saved memory found for this user."
