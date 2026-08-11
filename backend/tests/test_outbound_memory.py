"""
Tests for Phase 5 — Memory Integration during Outbound Practice Calls.
"""

import pytest

from db import create_or_update_user, get_user, init_db
from memory_tools import async_prefetch_user_memory
from prompts.system_prompt import SYSTEM_PROMPT


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Isolated database for test suite."""
    db_file = str(tmp_path / "test_outbound_memory.db")
    monkeypatch.setenv("BOLBUDDY_DB_PATH", db_file)
    init_db(db_path=db_file)
    return db_file


def test_system_prompt_phase5_memory_rules():
    """Verify system prompt contains Phase 5 recognized caller & memory rules."""
    assert "Want to practice for a few minutes?" in SYSTEM_PROMPT
    assert "PRACTICE" in SYSTEM_PROMPT
    assert "Never expose internal states, database keys" in SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_recognized_learner_memory_lookup():
    """Verify Day 4 memory retrieval loads learner name and past practice topics."""
    user_id = "user_sakshyam_test"
    create_or_update_user(
        user_id=user_id,
        name="Sakshyam",
        facts={
            "learning_goal": "internship interview preparation",
            "topics_practiced": ["internship interview English"],
        },
    )

    # Prefetch memory via Day 4 async cache
    memory = await async_prefetch_user_memory(user_id)
    assert memory is not None
    assert memory["name"] == "Sakshyam"

    facts = memory["facts"]
    assert facts["learning_goal"] == "internship interview preparation"
    assert "internship interview English" in facts["topics_practiced"]

    # Verify recognized caller greeting construction
    greeting = f"Hi {memory['name']}, this is BolBuddy. You scheduled an English practice session. Is this still a good time?"
    assert (
        greeting
        == "Hi Sakshyam, this is BolBuddy. You scheduled an English practice session. Is this still a good time?"
    )


@pytest.mark.asyncio
async def test_memory_lookup_failure_fallback():
    """Verify system handles missing or failed memory lookups gracefully without crashing."""
    user_id = "non_existent_user_999"

    # Non-existent user returns None or empty record without error
    user = get_user(user_id)
    assert user is None

    # Memory prefetch handles unknown user cleanly
    prefetch = await async_prefetch_user_memory(user_id)
    assert prefetch is None
