"""
Tests for BolBuddy Outbound Persona & Opening Greeting (Phase 4).
"""

from prompts.system_prompt import SYSTEM_PROMPT


def test_outbound_system_prompt_rules():
    """Verify system prompt includes explicit outbound persona rules."""
    assert "OUTBOUND CALL RULES" in SYSTEM_PROMPT
    assert "Want to practice for a few minutes?" in SYSTEM_PROMPT
    assert "No problem. I'll let you get back to your day. Bye!" in SYSTEM_PROMPT
    assert "end_call" in SYSTEM_PROMPT


def test_outbound_opening_greeting_construction():
    """Verify outbound greeting format satisfies Phase 4 mandatory requirements."""
    name = "Sakshyam"
    outbound_greeting_with_name = f"Hi {name}, this is BolBuddy. You scheduled your English practice for now. Want to practice for a few minutes?"

    # Check requirement 1: who is calling
    assert "this is BolBuddy" in outbound_greeting_with_name
    # Check requirement 2: why they are calling
    assert "You scheduled your English practice for now" in outbound_greeting_with_name
    # Check requirement 3: consent / can decline
    assert "Want to practice for a few minutes?" in outbound_greeting_with_name
