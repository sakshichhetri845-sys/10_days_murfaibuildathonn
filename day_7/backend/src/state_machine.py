"""
Deterministic Outbound Call State Machine for BolBuddy.

Python backend controls state transitions deterministically.
The LLM only generates natural language within the current state.
"""

import logging
from enum import Enum

logger = logging.getLogger("agent.state_machine")


class CallState(str, Enum):
    SCHEDULED = "SCHEDULED"
    CALLING = "CALLING"
    CONNECTED = "CONNECTED"
    GREETING = "GREETING"
    PRACTICE = "PRACTICE"
    FEEDBACK = "FEEDBACK"
    COMPLETED = "COMPLETED"
    NO_ANSWER = "NO_ANSWER"
    BUSY = "BUSY"
    VOICEMAIL = "VOICEMAIL"
    STOPPED = "STOPPED"


VALID_TRANSITIONS = {
    CallState.SCHEDULED: {CallState.CALLING, CallState.STOPPED},
    CallState.CALLING: {
        CallState.CONNECTED,
        CallState.NO_ANSWER,
        CallState.BUSY,
        CallState.VOICEMAIL,
        CallState.STOPPED,
    },
    CallState.CONNECTED: {CallState.GREETING, CallState.STOPPED},
    CallState.GREETING: {CallState.PRACTICE, CallState.STOPPED},
    CallState.PRACTICE: {CallState.FEEDBACK, CallState.STOPPED},
    CallState.FEEDBACK: {CallState.COMPLETED, CallState.STOPPED},
    CallState.COMPLETED: set(),
    CallState.NO_ANSWER: set(),
    CallState.BUSY: set(),
    CallState.VOICEMAIL: set(),
    CallState.STOPPED: set(),
}


class OutboundCallStateMachine:
    """
    Deterministic State Machine for managing BolBuddy Outbound Practice Calls.
    """

    def __init__(
        self, call_id: str, user_id: str, initial_state: CallState = CallState.SCHEDULED
    ):
        self.call_id = call_id
        self.user_id = user_id
        self.current_state = initial_state
        self.history: list[tuple[CallState, str]] = [(initial_state, "Initialization")]

    def transition_to(self, new_state: CallState, reason: str = "") -> bool:
        """Attempt deterministic state transition. Returns True if successful."""
        if new_state in VALID_TRANSITIONS.get(self.current_state, set()):
            logger.info(
                f"[CallState] {self.call_id}: {self.current_state.value} -> {new_state.value} ({reason})"
            )
            self.current_state = new_state
            self.history.append((new_state, reason))
            return True

        logger.warning(
            f"[CallState] Invalid transition attempted for {self.call_id}: "
            f"{self.current_state.value} -> {new_state.value} ({reason})"
        )
        return False

    def is_terminal(self) -> bool:
        """Return True if state machine is in a terminal state."""
        return self.current_state in {
            CallState.COMPLETED,
            CallState.NO_ANSWER,
            CallState.BUSY,
            CallState.VOICEMAIL,
            CallState.STOPPED,
        }
