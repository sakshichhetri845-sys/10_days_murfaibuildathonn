"""
Agent memory tools for HealthSathi Voice Agent with non-blocking asynchronous pre-fetching.

Provides LiveKit function tools for reading (lookup_user_memory) and writing (save_user_memory)
user memory through the persistent database layer (src/db.py).
"""

import asyncio
import json
import logging
from typing import Any, Optional

from livekit.agents import RunContext, function_tool

from db import (
    create_or_update_user,
    delete_user,
    get_user,
    record_health_preferences,
)

logger = logging.getLogger("agent.memory_tools")

# Session memory cache for non-blocking < 1ms retrieval
_USER_MEMORY_CACHE: dict[str, dict[str, Any]] = {}


def get_cached_user_memory(user_id: str) -> Optional[dict[str, Any]]:
    """Retrieve pre-fetched user memory from cache in < 1ms."""
    if not user_id:
        return None
    return _USER_MEMORY_CACHE.get(user_id)


def clear_memory_cache(user_id: Optional[str] = None) -> None:
    """Clear memory cache (useful for test isolation)."""
    if user_id:
        _USER_MEMORY_CACHE.pop(user_id, None)
    else:
        _USER_MEMORY_CACHE.clear()


async def async_prefetch_user_memory(
    user_id: str, timeout_seconds: float = 2.0
) -> Optional[dict[str, Any]]:
    """
    Asynchronously pre-fetch user memory in a background thread as soon as identity is known.
    Offloads SQLite file I/O off the asyncio event loop to prevent voice pipeline latency.
    """
    if not user_id:
        return None

    try:
        user_data = await asyncio.wait_for(
            asyncio.to_thread(get_user, user_id),
            timeout=timeout_seconds,
        )
        if user_data:
            _USER_MEMORY_CACHE[user_id] = user_data
        return user_data
    except asyncio.TimeoutError:
        logger.warning(
            f"Async memory prefetch timed out after {timeout_seconds}s for user_id: {user_id}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Async memory prefetch failed for user_id '{user_id}': {e}",
            exc_info=True,
        )
        return None


def _resolve_user_id(context: Optional[RunContext] = None, user_id: str = "") -> str:
    """Helper to extract user_id from explicit argument, userdata, or active LiveKit session context."""
    if (
        user_id
        and user_id.strip()
        and user_id.strip().lower() not in ("null", "none", "undefined", '""', "''")
    ):
        return user_id.strip()

    if context:
        try:
            ud = getattr(context, "userdata", None)
            if isinstance(ud, dict) and ud.get("user_id"):
                uid = ud.get("user_id")
                if uid and str(uid).strip().lower() not in (
                    "null",
                    "none",
                    "undefined",
                ):
                    return str(uid).strip()
        except Exception:
            pass

        try:
            sess = getattr(context, "session", None)
            if sess:
                sess_ud = getattr(sess, "userdata", None)
                if isinstance(sess_ud, dict) and sess_ud.get("user_id"):
                    uid = sess_ud.get("user_id")
                    if uid and str(uid).strip().lower() not in (
                        "null",
                        "none",
                        "undefined",
                    ):
                        return str(uid).strip()
                proc = getattr(sess, "proc", None)
                if proc:
                    pud = getattr(proc, "userdata", None)
                    if isinstance(pud, dict) and pud.get("user_id"):
                        uid = pud.get("user_id")
                        if uid and str(uid).strip().lower() not in (
                            "null",
                            "none",
                            "undefined",
                        ):
                            return str(uid).strip()
        except Exception:
            pass

        try:
            sess = getattr(context, "session", None)
            if sess:
                room_io = getattr(sess, "room_io", None)
                if room_io:
                    room = getattr(room_io, "room", None)
                    if (
                        room
                        and hasattr(room, "remote_participants")
                        and room.remote_participants
                    ):
                        participant = next(
                            iter(room.remote_participants.values()), None
                        )
                        if participant and getattr(participant, "identity", None):
                            return participant.identity
        except Exception:
            pass

    return "default_user"


@function_tool
async def lookup_user_memory(
    context: RunContext,
    user_id: str = "",
) -> str:
    """Look up saved user memory facts. Use only when needed to retrieve saved memory."""
    target_user_id = _resolve_user_id(context, user_id)
    if not target_user_id:
        logger.warning("lookup_user_memory: No user_id resolved")
        return "No saved memory found for this user."

    user_data = get_cached_user_memory(target_user_id)

    if not user_data:
        user_data = await async_prefetch_user_memory(
            target_user_id, timeout_seconds=1.5
        )

    if not user_data:
        return "No saved memory found for this user."

    facts = user_data.get("facts") or {}
    name = user_data.get("name")
    language_preference = user_data.get("language_preference")

    has_explicit_memory = (
        name is not None
        or language_preference is not None
        or bool(facts.get("reminder_preference"))
        or bool(facts.get("contact_preference"))
        or bool(facts.get("learning_goal"))
        or bool(facts.get("current_level"))
        or bool(facts.get("topics_practiced"))
    )

    if not has_explicit_memory:
        return "No saved memory found for this user."

    memory_info = {
        "name": name if name else None,
        "language_preference": language_preference if language_preference else None,
        "reminder_preference": facts.get("reminder_preference") or facts.get("learning_goal"),
        "contact_preference": facts.get("contact_preference"),
        "interaction_preferences": facts.get("interaction_preferences") or facts.get("topics_practiced", []),
    }

    filtered_memory = {k: v for k, v in memory_info.items() if v is not None}

    if not filtered_memory:
        return "No saved memory found for this user."

    return json.dumps(filtered_memory, ensure_ascii=False)


@function_tool
async def save_user_memory(
    context: RunContext,
    name: str = "",
    language_preference: str = "",
    reminder_preference: str = "",
    contact_preference: str = "",
    level: str = "",
    learning_goal: str = "",
    topic_practiced: str = "",
    recurring_challenge: str = "",
    user_id: str = "",
) -> str:
    """Save user memory facts (name, language, reminder preference, contact preference). Always require user consent before saving non-essential details."""
    target_user_id = _resolve_user_id(context, user_id)
    if not target_user_id:
        logger.warning("save_user_memory: No user_id resolved")
        return "Unable to save memory: No user identifier found."

    clean_name = name.strip() if name else None
    clean_lang = language_preference.strip() if language_preference else None
    clean_reminder = (reminder_preference or learning_goal or level).strip() if (reminder_preference or learning_goal or level) else None
    clean_contact = contact_preference.strip() if contact_preference else None
    clean_interaction = (topic_practiced or recurring_challenge).strip() if (topic_practiced or recurring_challenge) else None

    interaction_list = [clean_interaction] if clean_interaction else None

    updated_user = None

    if clean_name or clean_lang:
        updated_user = create_or_update_user(
            user_id=target_user_id,
            name=clean_name,
            language_preference=clean_lang,
        )

    if clean_reminder or clean_contact or interaction_list:
        updated_user = record_health_preferences(
            user_id=target_user_id,
            reminder_preference=clean_reminder,
            contact_preference=clean_contact,
            interaction_preferences=interaction_list,
        )

    if updated_user is None and not (
        clean_name or clean_lang or clean_reminder or clean_contact or interaction_list
    ):
        return "No memory fields were provided to save."

    if updated_user is None:
        return "Unable to save memory due to a database error."

    _USER_MEMORY_CACHE[target_user_id] = updated_user

    return "Memory saved successfully."


@function_tool
async def forget_my_data(
    context: RunContext,
    user_id: str = "",
) -> str:
    """Permanently delete user memory records.
    WHEN TO USE: ONLY after user explicitly confirms deletion (e.g. 'Yes', 'Delete it').
    WHEN NOT TO USE: DO NOT invoke unless user has explicitly confirmed deletion.
    INPUT: Optional user_id string.
    RETURNS: Deletion result status string.
    """
    target_user_id = _resolve_user_id(context, user_id)
    if not target_user_id:
        logger.warning("forget_my_data: No user_id resolved")
        return "Unable to delete memory: No user identifier found."

    # 1. Delete from persistent SQLite database
    success = delete_user(target_user_id)

    # 2. Clear from in-memory cache
    clear_memory_cache(target_user_id)

    if not success:
        logger.warning(
            f"forget_my_data: No database record found or deletion failed for user '{target_user_id}'"
        )
        return "No saved memory was found to delete or deletion could not be completed."

    return "Saved memory deleted successfully."


@function_tool
async def what_do_you_remember(
    context: RunContext,
    user_id: str,
) -> str:
    """Summarize saved memory for current user. RESPONSE RULE: Warmly explain saved memory facts (recalling name and goal) and ALWAYS end by offering: 'If you would ever like me to delete or forget any of your saved details, just let me know!'"""
    return await lookup_user_memory(context, user_id=user_id)
