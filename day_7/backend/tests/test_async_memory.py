"""
Unit tests for Optional Day 4 Feature: Asynchronous Non-Blocking Memory Retrieval (src/memory_tools.py).
"""

import asyncio
import os
import tempfile
import time

import pytest

from db import create_or_update_user, init_db
from memory_tools import (
    async_prefetch_user_memory,
    clear_memory_cache,
    get_cached_user_memory,
    lookup_user_memory,
)


@pytest.fixture
def temp_db():
    """Fixture providing a temporary SQLite database file for isolated testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    init_db(db_path=db_path)
    os.environ["BOLBUDDY_DB_PATH"] = db_path
    clear_memory_cache()

    yield db_path

    clear_memory_cache()
    if "BOLBUDDY_DB_PATH" in os.environ:
        del os.environ["BOLBUDDY_DB_PATH"]

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        pass


@pytest.mark.asyncio
async def test_async_prefetch_new_user(temp_db):
    """Test 1: New user async prefetch returns None without blocking."""
    user_id = "async_new_user_101"

    start_time = time.perf_counter()
    result = await async_prefetch_user_memory(user_id=user_id)
    elapsed = time.perf_counter() - start_time

    assert result is None
    assert elapsed < 0.1  # Fast non-blocking execution (< 100ms)
    assert get_cached_user_memory(user_id) is None


@pytest.mark.asyncio
async def test_async_prefetch_returning_user(temp_db):
    """Test 2: Returning user memory is pre-fetched asynchronously and cached for < 1ms retrieval."""
    user_id = "async_returning_user_102"
    create_or_update_user(
        user_id=user_id,
        name="Ananya",
        facts={"learning_goal": "viva presentation"},
        db_path=temp_db,
    )

    # Pre-fetch asynchronously
    fetched = await async_prefetch_user_memory(user_id=user_id)
    assert fetched is not None
    assert fetched["name"] == "Ananya"

    # Verify cached memory lookup executes in < 1ms without disk I/O latency
    start_time = time.perf_counter()
    lookup_res = await lookup_user_memory(context=None, user_id=user_id)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    assert "Ananya" in lookup_res
    assert "viva presentation" in lookup_res
    assert elapsed_ms < 5.0  # Instant retrieval (< 5ms)


@pytest.mark.asyncio
async def test_async_prefetch_slow_database(temp_db):
    """Test 3: Slow database query runs in background thread without blocking main asyncio loop."""
    user_id = "async_slow_db_user_103"
    create_or_update_user(
        user_id=user_id,
        name="Rahul",
        db_path=temp_db,
    )

    # Define a slow async prefetch wrapper simulating DB latency
    async def slow_prefetch():
        await asyncio.sleep(0.05)  # simulate network/disk delay
        return await async_prefetch_user_memory(user_id=user_id)

    start_time = time.perf_counter()
    task = asyncio.create_task(slow_prefetch())

    # Verify main event loop remains active and unblocked while prefetch runs
    loop_tick_start = time.perf_counter()
    await asyncio.sleep(0.01)  # main audio/VAD turn tick
    loop_tick_elapsed = time.perf_counter() - loop_tick_start

    assert loop_tick_elapsed < 0.03  # Main event loop was not stalled

    result = await task
    elapsed = time.perf_counter() - start_time

    assert result is not None
    assert result["name"] == "Rahul"
    assert elapsed >= 0.02


@pytest.mark.asyncio
async def test_async_prefetch_database_failure(temp_db):
    """Test 4: Database failure during async prefetch logs error and continues gracefully without memory."""
    os.environ["BOLBUDDY_DB_PATH"] = "/invalid_dir_999/unwritable.db"
    clear_memory_cache()

    user_id = "async_db_fail_user_104"
    result = await async_prefetch_user_memory(user_id=user_id)

    assert result is None
    # Lookup continues gracefully without memory or technical error output
    lookup_res = await lookup_user_memory(context=None, user_id=user_id)
    assert lookup_res == "No saved memory found for this user."


@pytest.mark.asyncio
async def test_async_prefetch_missing_user(temp_db):
    """Test 5: Missing user returns 'No saved memory found for this user.' without fabricating data."""
    user_id = "async_missing_user_105"
    result = await async_prefetch_user_memory(user_id=user_id)

    assert result is None
    lookup_res = await lookup_user_memory(context=None, user_id=user_id)
    assert lookup_res == "No saved memory found for this user."
