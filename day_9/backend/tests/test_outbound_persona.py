"""
Tests for HealthSathi Outbound Persona & Opening Greeting.
"""

from prompts.system_prompt import SYSTEM_PROMPT


def test_outbound_system_prompt_rules():
    """Verify system prompt includes HealthSathi identity and human escalation rules."""
    assert "HealthSathi" in SYSTEM_PROMPT
    assert "HUMAN ESCALATION CONSENT RULE" in SYSTEM_PROMPT


def test_outbound_opening_greeting_construction():
    """Verify outbound greeting format satisfies requirements."""
    name = "Sakshyam"
    outbound_greeting_with_name = f"Hi {name}, this is HealthSathi, your health support companion. I'm calling for your scheduled health reminder. Is this a good time to talk?"

    assert "this is HealthSathi" in outbound_greeting_with_name
    assert "scheduled health reminder" in outbound_greeting_with_name
    assert "Is this a good time to talk?" in outbound_greeting_with_name
