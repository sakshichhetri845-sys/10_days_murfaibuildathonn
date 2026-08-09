"""
Agent memory tools for BolBuddy Voice Agent with non-blocking asynchronous pre-fetching.

Provides LiveKit function tools for reading (lookup_user_memory) and writing (save_user_memory)
learner memory through the persistent database layer (src/db.py).
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
    record_learning_progress,
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
        # Offload DB I/O to background thread so main asyncio event loop / audio stream is NEVER blocked
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
        if hasattr(context, "userdata") and isinstance(context.userdata, dict):
            uid = context.userdata.get("user_id")
            if uid and str(uid).strip().lower() not in ("null", "none", "undefined"):
                return str(uid).strip()

        if hasattr(context, "session") and context.session:
            sess_ud = getattr(context.session, "userdata", None)
            if isinstance(sess_ud, dict) and sess_ud.get("user_id"):
                uid = sess_ud.get("user_id")
                if uid and str(uid).strip().lower() not in (
                    "null",
                    "none",
                    "undefined",
                ):
                    return str(uid).strip()

            room_io = getattr(context.session, "room_io", None)
            if room_io:
                room = getattr(room_io, "room", None)
                if (
                    room
                    and hasattr(room, "remote_participants")
                    and room.remote_participants
                ):
                    participant = next(iter(room.remote_participants.values()), None)
                    if participant and getattr(participant, "identity", None):
                        return participant.identity

    return "default_user"


@function_tool
async def lookup_user_memory(
    context: RunContext,
    user_id: str = "",
) -> str:
    """
    Look up saved learning memory for the current user.

    Use this tool when the user asks what you remember about them, their name, learning goals,
    current English level, topics practiced, or recurring challenges.

    Args:
        context: RunContext provided by the agent framework.
        user_id: Optional explicit user identifier.
    """
    target_user_id = _resolve_user_id(context, user_id)
    if not target_user_id:
        logger.warning("lookup_user_memory: No user_id resolved")
        return "No saved memory found for this user."

    # 1. Fast path: check in-memory cache (< 1ms)
    user_data = get_cached_user_memory(target_user_id)

    # 2. Fallback: if not in cache yet, perform non-blocking async prefetch
    if not user_data:
        user_data = await async_prefetch_user_memory(
            target_user_id, timeout_seconds=1.5
        )

    if not user_data:
        return "No saved memory found for this user."

    facts = user_data.get("facts") or {}
    name = user_data.get("name")
    language_preference = user_data.get("language_preference")

    # Only treat user as having saved memory if user-provided facts exist
    has_explicit_memory = (
        name is not None
        or language_preference is not None
        or bool(facts.get("topics_practiced"))
        or bool(facts.get("recurring_challenges"))
        or (
            facts.get("learning_goal")
            and facts.get("learning_goal") != "everyday conversation"
        )
    )

    if not has_explicit_memory:
        return "No saved memory found for this user."

    memory_info = {
        "name": name if name else None,
        "language_preference": language_preference if language_preference else None,
        "level": facts.get("current_level"),
        "learning_goal": facts.get("learning_goal"),
        "topics_practiced": facts.get("topics_practiced", []),
        "recurring_challenges": facts.get("recurring_challenges", []),
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
    level: str = "",
    learning_goal: str = "",
    topic_practiced: str = "",
    recurring_challenge: str = "",
    user_id: str = "",
) -> str:
    """
    Save or update memory facts for the current user.

    MANDATORY CONSENT RULE: Do NOT invoke this tool unless the user has given explicit verbal permission
    (e.g., 'yes', 'sure', 'okay', 'go ahead', 'remember it') to save/remember the specific fact.
    If the user declined ('no', 'don't save that') or gave an ambiguous response, DO NOT invoke this tool.

    Args:
        context: RunContext provided by the agent framework.
        name: Learner's preferred name.
        language_preference: Preferred language mode (e.g. English, Hinglish).
        level: Current English level (e.g. beginner, intermediate, advanced).
        learning_goal: Primary learning goal (e.g. job interview, college, viva, internship).
        topic_practiced: Specific topic practiced (e.g. self introduction).
        recurring_challenge: Concise qualitative challenge area (e.g. past tense).
        user_id: Optional explicit user identifier.
    """
    target_user_id = _resolve_user_id(context, user_id)
    if not target_user_id:
        logger.warning("save_user_memory: No user_id resolved")
        return "Unable to save memory: No user identifier found."

    clean_name = name.strip() if name else None
    clean_lang = language_preference.strip() if language_preference else None
    clean_level = level.strip() if level else None
    clean_goal = learning_goal.strip() if learning_goal else None
    clean_topic = topic_practiced.strip() if topic_practiced else None
    clean_challenge = recurring_challenge.strip() if recurring_challenge else None

    topics_list = [clean_topic] if clean_topic else None
    challenges_list = [clean_challenge] if clean_challenge else None

    updated_user = None

    if clean_name or clean_lang:
        updated_user = create_or_update_user(
            user_id=target_user_id,
            name=clean_name,
            language_preference=clean_lang,
        )

    if clean_level or clean_goal or topics_list or challenges_list:
        updated_user = record_learning_progress(
            user_id=target_user_id,
            current_level=clean_level,
            learning_goal=clean_goal,
            topics_practiced=topics_list,
            recurring_challenges=challenges_list,
        )

    if updated_user is None and not (
        clean_name
        or clean_lang
        or clean_level
        or clean_goal
        or topics_list
        or challenges_list
    ):
        return "No memory fields were provided to save."

    if updated_user is None:
        return "Unable to save memory due to a database error."

    # Update cache immediately on save
    _USER_MEMORY_CACHE[target_user_id] = updated_user

    return "Memory saved successfully."


@function_tool
async def forget_my_data(
    context: RunContext,
    user_id: str = "",
) -> str:
    """
    Permanently delete or reset all saved memory and learning records for the current user.

    MANDATORY CONFIRMATION RULE: Do NOT invoke this tool unless the user has explicitly confirmed
    their request to delete, reset, clear, or forget their saved memory (e.g. 'Yes', 'Sure', 'Delete it', 'Reset it', 'Go ahead').
    If the user has not confirmed or has declined ('No', 'Keep my data'), DO NOT invoke this tool.

    Args:
        context: RunContext provided by the agent framework.
        user_id: Optional explicit user identifier.
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
    user_id: str = "",
) -> str:
    """
    Retrieve and summarize what BolBuddy currently remembers about the user.

    Use this tool when the user asks 'What do you remember about me?', 'What have you saved about me?',
    'Do you remember my goal?', or asks to review their stored profile facts.

    Args:
        context: RunContext provided by the agent framework.
        user_id: Optional explicit user identifier.
    """
    return await lookup_user_memory(context, user_id=user_id)
