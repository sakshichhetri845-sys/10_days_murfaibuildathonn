"""
Groq API Key Manager for BolBuddy Voice Agent.

Manages a pool of Groq API keys with automatic failover and rate-limit cooldown.
"""

import logging
import os
import time
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple
import openai

logger = logging.getLogger(__name__)


class GroqKeyManager:
    """Thread-safe manager for multiple Groq API keys with automatic failover and cooldown."""

    def __init__(self, cooldown_seconds: Optional[float] = None) -> None:
        self._lock = Lock()
        if cooldown_seconds is None:
            try:
                cooldown_seconds = float(os.getenv("GROQ_KEY_COOLDOWN_SECONDS", "60"))
            except ValueError:
                cooldown_seconds = 60.0
        self.cooldown_seconds: float = cooldown_seconds
        self._keys: List[str] = []
        self._rate_limited_until: Dict[int, float] = {}  # 1-based key index -> timestamp
        self._active_index: int = 1  # 1-based index
        self._clients: Dict[str, openai.AsyncClient] = {}
        self.reload_keys()

    def reload_keys(self) -> None:
        """Load GROQ_API_KEY_1..N and fallback GROQ_API_KEY from environment."""
        with self._lock:
            keys: List[str] = []
            # Check GROQ_API_KEY_1 through GROQ_API_KEY_10
            for i in range(1, 11):
                k = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
                if k and k not in keys:
                    keys.append(k)

            # Fallback GROQ_API_KEY if no indexed keys found or to include it
            fallback_k = os.getenv("GROQ_API_KEY", "").strip()
            if fallback_k and fallback_k not in keys:
                keys.append(fallback_k)

            self._keys = keys
            self._rate_limited_until.clear()
            self._active_index = 1 if self._keys else 0

            if self._keys:
                logger.info(f"Groq key pool initialized: {len(self._keys)} keys available")
            else:
                logger.error("ERROR: No Groq API keys configured.")

    @property
    def key_count(self) -> int:
        """Return total number of loaded keys."""
        with self._lock:
            return len(self._keys)

    def is_key_available(self, index_1based: int) -> bool:
        """Check if a 1-based key index is available (not currently in rate-limit cooldown)."""
        if index_1based < 1 or index_1based > len(self._keys):
            return False
        until = self._rate_limited_until.get(index_1based, 0.0)
        return time.time() >= until

    def get_active_key(self) -> Tuple[int, str]:
        """Return (1-based_index, key_str) of the highest-priority available key.

        Prefers Key 1, then Key 2, etc. If all keys are rate-limited, returns the key with the earliest expiration.
        """
        with self._lock:
            if not self._keys:
                raise RuntimeError("No Groq API keys available in environment.")

            now = time.time()
            total = len(self._keys)

            # Always check from primary (Key 1) to lowest priority key
            for idx in range(1, total + 1):
                until = self._rate_limited_until.get(idx, 0.0)
                if now >= until:
                    self._active_index = idx
                    return idx, self._keys[idx - 1]

            # If all keys are rate-limited, find key with earliest cooldown expiry
            earliest_idx = min(
                range(1, total + 1),
                key=lambda i: self._rate_limited_until.get(i, float("inf")),
            )
            self._active_index = earliest_idx
            return earliest_idx, self._keys[earliest_idx - 1]

    def mark_key_rate_limited(self, index_1based: int) -> int:
        """Mark a key rate-limited for cooldown_seconds and advance to the next available key.

        Returns the new active key index.
        """
        with self._lock:
            if 1 <= index_1based <= len(self._keys):
                expiry = time.time() + self.cooldown_seconds
                self._rate_limited_until[index_1based] = expiry

            total = len(self._keys)
            now = time.time()
            # Advance to next available key index
            for offset in range(1, total + 1):
                next_idx = ((index_1based - 1 + offset) % total) + 1
                until = self._rate_limited_until.get(next_idx, 0.0)
                if now >= until:
                    self._active_index = next_idx
                    return next_idx

            # If all are in cooldown, cycle to next index anyway
            self._active_index = (index_1based % total) + 1
            return self._active_index

    def get_groq_key_status(self) -> List[Dict[str, Any]]:
        """Return status list for health diagnostics."""
        with self._lock:
            now = time.time()
            status = []
            for i in range(1, len(self._keys) + 1):
                until = self._rate_limited_until.get(i, 0.0)
                status.append(
                    {
                        "key": i,
                        "available": now >= until,
                        "cooldown_remaining_sec": max(0.0, round(until - now, 1)),
                    }
                )
            return status

    def get_client_for_key(self, key_str: str) -> openai.AsyncClient:
        """Return cached openai.AsyncClient for given key string."""
        with self._lock:
            if key_str not in self._clients:
                self._clients[key_str] = openai.AsyncClient(
                    api_key=key_str,
                    base_url="https://api.groq.com/openai/v1",
                )
            return self._clients[key_str]


# Global singleton instance
groq_key_manager = GroqKeyManager()
