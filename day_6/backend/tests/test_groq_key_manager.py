"""
Unit tests for Groq Key Manager and Multi-Key Failover behavior.
"""

import time

# pyrefly: ignore [missing-import]
from src.groq_key_manager import GroqKeyManager


def test_groq_key_manager_load_and_rotation(monkeypatch) -> None:
    """Test key loading, missing key handling, rate-limit failover, and cooldown recovery."""
    # Set mock environment variables
    monkeypatch.setenv("GROQ_API_KEY_1", "mock_key_one")
    monkeypatch.setenv("GROQ_API_KEY_2", "mock_key_two")
    monkeypatch.setenv("GROQ_API_KEY_3", "mock_key_three")
    monkeypatch.delenv("GROQ_API_KEY_4", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    manager = GroqKeyManager(cooldown_seconds=1.0)
    assert manager.key_count == 3

    # Initial active key should be index 1
    idx1, key1 = manager.get_active_key()
    assert idx1 == 1
    assert key1 == "mock_key_one"

    # Simulate rate-limit on Key 1
    next_idx = manager.mark_key_rate_limited(1)
    assert next_idx == 2

    # Active key should now be index 2
    idx2, key2 = manager.get_active_key()
    assert idx2 == 2
    assert key2 == "mock_key_two"

    # Simulate rate-limit on Key 2
    next_idx2 = manager.mark_key_rate_limited(2)
    assert next_idx2 == 3

    idx3, key3 = manager.get_active_key()
    assert idx3 == 3
    assert key3 == "mock_key_three"

    # Check status report
    status = manager.get_groq_key_status()
    assert len(status) == 3
    assert status[0]["available"] is False
    assert status[1]["available"] is False
    assert status[2]["available"] is True

    # Wait for cooldown (1.0 sec)
    time.sleep(1.1)

    # After cooldown, Key 1 should be available again
    assert manager.is_key_available(1) is True
    idx_after, key_after = manager.get_active_key()
    assert idx_after == 1
    assert key_after == "mock_key_one"


def test_groq_key_manager_fallback(monkeypatch) -> None:
    """Test backward compatibility fallback to single GROQ_API_KEY."""
    monkeypatch.delenv("GROQ_API_KEY_1", raising=False)
    monkeypatch.delenv("GROQ_API_KEY_2", raising=False)
    monkeypatch.delenv("GROQ_API_KEY_3", raising=False)
    monkeypatch.delenv("GROQ_API_KEY_4", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "fallback_single_key")

    manager = GroqKeyManager()
    assert manager.key_count == 1
    idx, key = manager.get_active_key()
    assert idx == 1
    assert key == "fallback_single_key"
