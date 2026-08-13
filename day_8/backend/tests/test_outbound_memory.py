"""
Tests for Memory Integration during Outbound Health Reminder Calls for HealthSathi.
"""

import pytest

from db import create_or_update_user, init_db
from memory_tools import async_prefetch_user_memory
from prompts.system_prompt import SYSTEM_PROMPT


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Isolated database for test suite."""
    db_file = str(tmp_path / "test_outbound_memory.db")
    monkeypatch.setenv("HEALTHSATHI_DB_PATH", db_file)
    init_db(db_path=db_file)
    return db_file


def test_system_prompt_health_rules():
    """Verify system prompt contains HealthSathi identity & memory rules."""
    assert "HealthSathi" in SYSTEM_PROMPT
    assert "HUMAN ESCALATION CONSENT RULE" in SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_recognized_user_memory_lookup():
    """Verify memory retrieval loads user name and reminder preferences."""
    user_id = "user_sakshyam_test"
    create_or_update_user(
        user_id=user_id,
        name="Sakshyam",
        facts={
            "reminder_preference": "Medication reminder 8am",
        },
    )

    memory = await async_prefetch_user_memory(user_id)
    assert memory is not None
    assert memory["name"] == "Sakshyam"
    assert memory["facts"]["reminder_preference"] == "Medication reminder 8am"

    greeting = f"Hi {memory['name']}, this is HealthSathi, your health support companion."
    assert greeting == "Hi Sakshyam, this is HealthSathi, your health support companion."


@pytest.mark.asyncio
async def test_memory_lookup_failure_fallback():
    """Verify system handles missing or failed memory lookups gracefully without crashing."""
    memory = await async_prefetch_user_memory("non_existent_user_xyz")
    assert memory is None
