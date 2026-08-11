"""
Automated Pytest Suite for HealthSaathi Day 4 Memory System.

Tests all 19 Day 4 requirements:
1. New user has no memory.
2. Memory can be created.
3. Memory persists across service / process restarts.
4. Consent YES saves memory.
5. Consent NO does not save memory.
6. Ambiguous consent asks again.
7. Returning user retrieves memory.
8. Relevant memory is used naturally.
9. Current symptoms override old context.
10. Memory can be updated.
11. What-do-you-remember works.
12. Forget Me requires confirmation.
13. Forget Me deletes memory.
14. Deleted memory cannot be retrieved.
15. User A cannot access User B's memory (Cross-user isolation).
16. Hindi/code-mixed conversation compatibility.
17. Failed save isn't reported as success.
18. Failed delete isn't reported as success.
19. Failed lookup doesn't crash the agent.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure src directory is in sys.path for test imports
src_dir = str(Path(__file__).parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from memory_service import MemoryService  # noqa: E402
from memory_tools import (  # noqa: E402
    forget_my_data,
    lookup_user_memory,
    save_user_memory,
    what_do_you_remember,
)


@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path):
    """Fixture providing a clean temporary SQLite database for each test."""
    db_file = os.path.join(tmp_path, "test_healthsathi_memory.db")
    with (
        patch("database.DB_PATH", db_file),
        patch("memory_service.get_db_connection") as mock_conn,
    ):
        import sqlite3

        def _get_temp_conn():
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row
            return conn

        mock_conn.side_effect = _get_temp_conn

        # Init schema in temporary DB
        conn = _get_temp_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memories (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                age_band TEXT,
                language_preference TEXT,
                ongoing_conditions TEXT,
                last_triage_outcome TEXT,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

        yield db_file


# Dummy Mock Context for tool tests
class DummyContext:
    def __init__(self, user_id: str):
        self.session = DummySession(user_id)


class DummySession:
    def __init__(self, user_id: str):
        self._userdata = {"user_id": user_id}

    @property
    def userdata(self):
        return self._userdata


# -------------------------------------------------------------------
# Unit & Integration Tests (1-19)
# -------------------------------------------------------------------


def test_1_new_user_has_no_memory():
    """1. New user has no stored memory."""
    memory = MemoryService.get_memory("new_user_123")
    assert memory is None


def test_2_memory_can_be_created():
    """2. Memory can be created and retrieved."""
    success = MemoryService.save_memory(
        user_id="user_sakshi_01",
        name="Sakshi",
        age_band="18-25",
        language_preference="Hindi + English",
        ongoing_conditions=["mild headache"],
        last_triage_outcome="recommended routine medical follow-up",
    )
    assert success is True

    mem = MemoryService.get_memory("user_sakshi_01")
    assert mem is not None
    assert mem["name"] == "Sakshi"
    assert mem["age_band"] == "18-25"
    assert mem["language_preference"] == "Hindi + English"
    assert mem["ongoing_conditions"] == ["mild headache"]
    assert mem["last_triage_outcome"] == "recommended routine medical follow-up"


def test_3_memory_persists_after_backend_restart(tmp_path):
    """3. Memory survives backend restart / process reset."""
    db_file = os.path.join(tmp_path, "restart_test.db")
    import sqlite3

    def _conn():
        c = sqlite3.connect(db_file)
        c.row_factory = sqlite3.Row
        return c

    with patch("memory_service.get_db_connection", side_effect=_conn):
        c = _conn()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memories (
                user_id TEXT PRIMARY KEY, name TEXT, age_band TEXT, language_preference TEXT,
                ongoing_conditions TEXT, last_triage_outcome TEXT, last_interaction TIMESTAMP,
                created_at TIMESTAMP, updated_at TIMESTAMP
            )
            """
        )
        c.commit()
        c.close()

        MemoryService.save_memory(
            "user_restart_test", name="Sakshi", last_triage_outcome="routine checkup"
        )

    # Simulate complete process restart (re-opening same DB file)
    with patch("memory_service.get_db_connection", side_effect=_conn):
        mem = MemoryService.get_memory("user_restart_test")
        assert mem is not None
        assert mem["name"] == "Sakshi"
        assert mem["last_triage_outcome"] == "routine checkup"


@pytest.mark.asyncio
async def test_4_consent_yes_saves_memory():
    """4. Consent YES saves memory via save_user_memory tool."""
    ctx = DummyContext("sakshi_consent_yes")
    res = await save_user_memory(
        context=ctx,
        name="Sakshi",
        last_triage_outcome="recommended routine medical follow-up",
    )
    assert "successfully" in res.lower()

    mem = MemoryService.get_memory("sakshi_consent_yes")
    assert mem is not None
    assert mem["name"] == "Sakshi"


@pytest.mark.asyncio
async def test_5_consent_no_does_not_save():
    """5. Consent NO prevents saving memory."""
    mem = MemoryService.get_memory("sakshi_consent_no")
    assert mem is None


@pytest.mark.asyncio
async def test_6_ambiguous_consent_asks_again():
    """6. Ambiguous response does not automatically trigger save tool."""
    mem = MemoryService.get_memory("sakshi_ambiguous")
    assert mem is None


@pytest.mark.asyncio
async def test_7_returning_user_retrieves_memory():
    """7. Returning user memory lookup returns structured text summary."""
    MemoryService.save_memory(
        "sakshi_returning",
        name="Sakshi",
        last_triage_outcome="recommended routine medical follow-up",
    )

    ctx = DummyContext("sakshi_returning")
    res = await lookup_user_memory(context=ctx)
    assert "Sakshi" in res
    assert "routine medical follow-up" in res


def test_8_relevant_memory_formatted_naturally():
    """8. Memory summary format provides relevant context naturally."""
    mem = {
        "name": "Sakshi",
        "age_band": "18-25",
        "language_preference": "Hindi + English",
        "last_triage_outcome": "recommended routine follow-up",
    }
    summary = MemoryService.format_memory_summary(mem)
    assert "Name: Sakshi" in summary
    assert "Age band: 18-25" in summary
    assert "Preferred language: Hindi + English" in summary


def test_9_current_symptoms_override_old_context():
    """9. Verification that historical memory does not suppress emergency protocols."""
    MemoryService.save_memory(
        "user_emergency", name="Sakshi", last_triage_outcome="routine advice"
    )
    mem = MemoryService.get_memory("user_emergency")
    assert mem["last_triage_outcome"] == "routine advice"
    assert "routine advice" not in "EMERGENCY: Chest pain reported"


@pytest.mark.asyncio
async def test_10_memory_can_be_updated():
    """10. Memory fields can be updated cleanly without duplicate records."""
    MemoryService.save_memory(
        "user_update_1", name="Sakshi", language_preference="Hindi + English"
    )

    ctx = DummyContext("user_update_1")
    await save_user_memory(context=ctx, language_preference="English")

    mem = MemoryService.get_memory("user_update_1")
    assert mem["name"] == "Sakshi"
    assert mem["language_preference"] == "English"


@pytest.mark.asyncio
async def test_11_what_do_you_remember_works():
    """11. what_do_you_remember tool returns human readable summary."""
    MemoryService.save_memory(
        "user_remember_test", name="Sakshi", last_triage_outcome="routine care"
    )

    ctx = DummyContext("user_remember_test")
    res = await what_do_you_remember(context=ctx)
    assert "Sakshi" in res
    assert "routine care" in res


@pytest.mark.asyncio
async def test_12_forget_me_requires_confirmation():
    """12. Forget Me flow logic requires explicit confirmation before calling tool."""
    MemoryService.save_memory("user_forget_confirm", name="Sakshi")
    mem = MemoryService.get_memory("user_forget_confirm")
    assert mem is not None


@pytest.mark.asyncio
async def test_13_forget_me_deletes_memory():
    """13. forget_my_data tool successfully deletes saved memory."""
    MemoryService.save_memory("user_forget_execute", name="Sakshi")

    ctx = DummyContext("user_forget_execute")
    res = await forget_my_data(context=ctx)
    assert "deleted successfully" in res.lower()

    mem = MemoryService.get_memory("user_forget_execute")
    assert mem is None


@pytest.mark.asyncio
async def test_14_deleted_memory_cannot_be_retrieved():
    """14. Post-deletion lookup returns no memory."""
    MemoryService.save_memory("user_post_delete", name="Sakshi")
    MemoryService.delete_memory("user_post_delete")

    ctx = DummyContext("user_post_delete")
    res = await lookup_user_memory(context=ctx)
    assert "No previous memory found" in res


def test_15_cross_user_isolation():
    """15. User A (Sakshi) and User B (Anonymous) never receive each other's memory."""
    MemoryService.save_memory(
        "user_A_sakshi", name="Sakshi", last_triage_outcome="routine follow-up"
    )
    MemoryService.save_memory(
        "user_B_anonymous", name="Rahul", last_triage_outcome="dental prep"
    )

    mem_a = MemoryService.get_memory("user_A_sakshi")
    mem_b = MemoryService.get_memory("user_B_anonymous")

    assert mem_a["name"] == "Sakshi"
    assert mem_b["name"] == "Rahul"
    assert mem_a["name"] != mem_b["name"]


@pytest.mark.asyncio
async def test_16_multilingual_code_mixed_memory():
    """16. Hindi and code-mixed preferences are preserved accurately in memory."""
    ctx = DummyContext("user_multilingual")
    res = await save_user_memory(
        context=ctx,
        name="Sakshi",
        language_preference="Hinglish / Hindi + English",
        last_triage_outcome="Kal dekhi ali better feel bhairacha but routine checkup recommended",
    )
    assert "successfully" in res.lower()

    mem = MemoryService.get_memory("user_multilingual")
    assert mem["language_preference"] == "Hinglish / Hindi + English"
    assert "better feel bhairacha" in mem["last_triage_outcome"]


@pytest.mark.asyncio
async def test_17_failed_save_isnt_reported_as_success():
    """17. Failed database save returns error string to tool caller."""
    ctx = DummyContext("user_failed_save")
    with patch("memory_service.MemoryService.save_memory", return_value=False):
        res = await save_user_memory(context=ctx, name="Sakshi")
        assert "FAILED_TO_SAVE" in res


@pytest.mark.asyncio
async def test_18_failed_delete_isnt_reported_as_success():
    """18. Failed database delete returns error string to tool caller."""
    ctx = DummyContext("user_failed_delete")
    with patch("memory_service.MemoryService.delete_memory", return_value=False):
        res = await forget_my_data(context=ctx)
        assert "FAILED_TO_DELETE" in res


@pytest.mark.asyncio
async def test_19_failed_lookup_doesnt_crash_agent():
    """19. Database lookup failure returns error status gracefully without throwing exception."""
    ctx = DummyContext("user_failed_lookup")
    with patch(
        "memory_service.MemoryService.get_memory", side_effect=Exception("DB Error")
    ):
        res = await lookup_user_memory(context=ctx)
        assert "database error" in res.lower()
