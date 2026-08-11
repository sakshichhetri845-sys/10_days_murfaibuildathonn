"""
Memory Tools for HealthSaathi Voice Agent.
LiveKit @function_tool endpoints for memory lookup, save, delete, and status.
"""

import logging
from typing import Optional

from livekit.agents import RunContext, function_tool

try:
    from src.memory_service import MemoryService
except ImportError:
    from memory_service import MemoryService

logger = logging.getLogger("healthsathi.memory_tools")


def get_current_user_id(context: RunContext) -> str:
    """
    Resolve a stable user_id from the RunContext.
    Priority: session.userdata → room participant identity → fallback string.
    """
    # 1. Read from session.userdata (set via AgentSession(userdata=...) in agent.py)
    try:
        ud = context.session.userdata
        if isinstance(ud, dict) and ud.get("user_id"):
            return str(ud["user_id"])
    except Exception:
        pass

    # 2. Fall back to first remote participant identity in the room
    try:
        room = context.session.room
        if room:
            for p in room.remote_participants.values():
                if p.identity:
                    return p.identity
    except Exception:
        pass

    return "anonymous_user"


@function_tool
async def lookup_user_memory(
    context: RunContext,
    query: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Look up stored memory for the current user.

    Call this at the start of a session to check for a returning user's name,
    language preference, or previous health guidance.

    Args:
        query: Optional keyword hint (e.g. 'name', 'conditions').
        user_id: Optional explicit user_id.
    """
    uid = user_id or get_current_user_id(context)
    logger.info(f"lookup_user_memory called — user_id={uid}")
    try:
        memory = MemoryService.get_memory(uid)
        if not memory:
            return "No previous memory found for this user."
        return MemoryService.format_memory_summary(memory)
    except Exception as e:
        logger.error(f"lookup_user_memory failed for user_id={uid}: {e}")
        return "Failed to lookup memory due to a database error."


@function_tool
async def save_user_memory(
    context: RunContext,
    name: Optional[str] = None,
    age_band: Optional[str] = None,
    language_preference: Optional[str] = None,
    ongoing_conditions: Optional[list[str]] = None,
    last_triage_outcome: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Save or update memory for the current user.

    CONSENT RULE: Only call this after the user has explicitly said "Yes" to saving
    their information. Never call this without confirmed consent.
    """
    uid = user_id or get_current_user_id(context)
    logger.info(f"save_user_memory called — user_id={uid}")
    success = MemoryService.save_memory(
        user_id=uid,
        name=name,
        age_band=age_band,
        language_preference=language_preference,
        ongoing_conditions=ongoing_conditions,
        last_triage_outcome=last_triage_outcome,
    )
    if success:
        return "Memory saved successfully."
    return "FAILED_TO_SAVE: Database error. Do not tell the user their data was saved."


@function_tool
async def forget_my_data(
    context: RunContext,
    reason: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Delete all stored memory for the current user.

    CONFIRMATION RULE: Only call this after the user has explicitly confirmed
    they want their data deleted.
    """
    uid = user_id or get_current_user_id(context)
    logger.info(f"forget_my_data called — user_id={uid}")
    success = MemoryService.delete_memory(uid)
    if success:
        return "Memory deleted successfully."
    return (
        "FAILED_TO_DELETE: Database error. Do not tell the user their data was deleted."
    )


@function_tool
async def what_do_you_remember(
    context: RunContext,
    topic: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Tell the user what HealthSaathi currently remembers about them.
    """
    uid = user_id or get_current_user_id(context)
    logger.info(f"what_do_you_remember called — user_id={uid}")
    try:
        memory = MemoryService.get_memory(uid)
        if not memory or not any(
            [
                memory.get("name"),
                memory.get("age_band"),
                memory.get("last_triage_outcome"),
                memory.get("ongoing_conditions"),
            ]
        ):
            return "I don't currently have any saved information about you."
        return MemoryService.format_memory_summary(memory)
    except Exception as e:
        logger.error(f"what_do_you_remember failed for user_id={uid}: {e}")
        return "Unable to retrieve memory status at the moment."


@function_tool
async def end_call(
    context: RunContext,
) -> str:
    """
    Disconnects and ends the SIP telephony or practice call immediately.

    Call this tool immediately when:
    - Learner declines or is busy ("no", "not now", "busy")
    - Learner requests opt-out / stop calling ("stop calling", "remove my number")
    - Wrong number ("wrong number", "not [Name]")
    - Voicemail or automated machine detected
    """
    logger.info("end_call tool executed — disconnecting room session")
    try:
        if hasattr(context.session, "aclose"):
            await context.session.aclose()
        elif hasattr(context.session, "room"):
            await context.session.room.disconnect()
        return "Call disconnected successfully."
    except Exception as e:
        logger.error(f"Error in end_call tool: {e}")
        return "Failed to disconnect call cleanly."
