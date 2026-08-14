"""
Unit and safety boundary test suite for HealthSathi Voice Agent (Phase 4 Medical Safety Rules).
"""

from prompts.guardrails import GUARDRAILS
from prompts.identity import IDENTITY


def test_safety_guardrails_contain_non_diagnostic_rules():
    """Verify that guardrails explicitly contain non-diagnostic, non-prescriptive, and emergency escalation rules."""
    assert "NON-DIAGNOSTIC" in GUARDRAILS
    assert "NO PRESCRIPTIONS" in GUARDRAILS
    assert "EMERGENCY PRIORITIZATION" in GUARDRAILS
    assert "DO NOT IGNORE SYMPTOMS" in GUARDRAILS


def test_healthsathi_identity_boundaries():
    """Verify identity module explicitly includes non-doctor boundaries."""
    assert "You are NOT a doctor" in IDENTITY
    assert "never claim to diagnose" in IDENTITY.lower()
    assert "never prescribe medication" in IDENTITY.lower()
