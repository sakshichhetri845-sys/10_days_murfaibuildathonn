"""
Unit tests for Layer 2 Deterministic Call State Machine.
"""

from state_machine import CallState, OutboundCallStateMachine


def test_valid_state_transitions():
    """Verify valid deterministic state transitions."""
    sm = OutboundCallStateMachine(call_id="call_sm_1", user_id="user_sm_1")
    assert sm.current_state == CallState.SCHEDULED

    # SCHEDULED -> CALLING
    assert (
        sm.transition_to(CallState.CALLING, "Dispatching LiveKit SIP participant")
        is True
    )
    assert sm.current_state == CallState.CALLING

    # CALLING -> CONNECTED
    assert sm.transition_to(CallState.CONNECTED, "Learner answered phone") is True
    assert sm.current_state == CallState.CONNECTED

    # CONNECTED -> GREETING
    assert sm.transition_to(CallState.GREETING, "Opening greeting delivered") is True
    assert sm.current_state == CallState.GREETING

    # GREETING -> PRACTICE
    assert sm.transition_to(CallState.PRACTICE, "Learner agreed to practice") is True
    assert sm.current_state == CallState.PRACTICE

    # PRACTICE -> FEEDBACK
    assert sm.transition_to(CallState.FEEDBACK, "Practice question answered") is True
    assert sm.current_state == CallState.FEEDBACK

    # FEEDBACK -> COMPLETED
    assert sm.transition_to(CallState.COMPLETED, "Practice session completed") is True
    assert sm.current_state == CallState.COMPLETED
    assert sm.is_terminal() is True


def test_invalid_arbitrary_transitions_blocked():
    """Verify invalid arbitrary state transitions are rejected by backend state machine."""
    sm = OutboundCallStateMachine(call_id="call_sm_2", user_id="user_sm_2")
    assert sm.current_state == CallState.SCHEDULED

    # Cannot transition directly from SCHEDULED to FEEDBACK or COMPLETED
    assert sm.transition_to(CallState.FEEDBACK, "LLM attempt") is False
    assert sm.current_state == CallState.SCHEDULED
    assert sm.transition_to(CallState.COMPLETED, "LLM attempt") is False
    assert sm.current_state == CallState.SCHEDULED


def test_stop_transitions():
    """Verify STOPPED transition from any active state."""
    sm = OutboundCallStateMachine(call_id="call_sm_3", user_id="user_sm_3")
    sm.transition_to(CallState.CALLING)
    sm.transition_to(CallState.CONNECTED)
    sm.transition_to(CallState.GREETING)

    # Learner says "I'm busy" / "stop calling"
    assert sm.transition_to(CallState.STOPPED, "Learner requested stop") is True
    assert sm.current_state == CallState.STOPPED
    assert sm.is_terminal() is True
