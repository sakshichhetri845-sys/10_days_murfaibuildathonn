"""
Master Final Integration Test Suite for HealthSathi Voice Agent.

Executes end-to-end user scenario and failure recovery tests.
"""

import os
import tempfile

import pytest
from livekit.agents import inference, llm

from db import get_user, init_db
from memory_tools import (
    clear_memory_cache,
    forget_my_data,
    lookup_user_memory,
    save_user_memory,
)


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.fixture
def master_db():
    """Fixture providing a clean temporary SQLite database file for master integration testing."""
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
async def test_master_day4_integration_flow(master_db):
    """
    Executes HealthSathi end-to-end integration scenario across calls.
    """
    user_id = "master_user_ramesh_404"

    # CALL 1: NEW USER SESSION & CONSENT SAVING
    res_initial = await lookup_user_memory(context=None, user_id=user_id)
    assert res_initial == "No saved memory found for this user."

    save_res = await save_user_memory(
        context=None,
        name="Sakshyam",
        language_preference="Hinglish",
        reminder_preference="Daily medication reminder at 8am",
        user_id=user_id,
    )
    assert save_res == "Memory saved successfully."

    rec_c1 = get_user(user_id=user_id, db_path=master_db)
    assert rec_c1 is not None
    assert rec_c1["name"] == "Sakshyam"
    assert rec_c1["facts"]["reminder_preference"] == "Daily medication reminder at 8am"

    # BACKEND RESTART SIMULATION
    clear_memory_cache()
    disk_rec = get_user(user_id=user_id, db_path=master_db)
    assert disk_rec is not None
    assert disk_rec["user_id"] == user_id

    # CALL 2: RETURNING USER SESSION
    lookup_res = await lookup_user_memory(context=None, user_id=user_id)
    assert lookup_res != "No saved memory found for this user."

    # CALL 3: MEMORY DELETION REQUEST
    del_res = await forget_my_data(context=None, user_id=user_id)
    assert del_res == "Saved memory deleted successfully."

    after_del = get_user(user_id=user_id, db_path=master_db)
    assert after_del is None
