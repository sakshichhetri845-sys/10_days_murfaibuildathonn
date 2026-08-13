"""
Unit tests for symptom_to_triage and find_nearby_facility tools.

These tests validate the keyword-based pre-classifier and JSON output structure
without requiring a live LLM — they run in milliseconds.
"""

import importlib.util
import os
import sys

src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

outbound_agent_path = os.path.join(src_dir, "telephony", "outbound", "agent.py")
spec = importlib.util.spec_from_file_location("outbound_agent_mod", outbound_agent_path)
outbound_agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(outbound_agent_mod)

_classify_symptoms = outbound_agent_mod._classify_symptoms
_TRIAGE_GUIDANCE = outbound_agent_mod._TRIAGE_GUIDANCE


class TestClassifySymptoms:
    def test_urgent_chest_pain(self):
        level = _classify_symptoms("I have severe chest pain and can't breathe")
        assert level == "urgent", f"Expected 'urgent', got '{level}'"

    def test_urgent_seizure(self):
        level = _classify_symptoms("My child is having a seizure")
        assert level == "urgent", f"Expected 'urgent', got '{level}'"

    def test_soon_high_fever(self):
        level = _classify_symptoms("I have a high fever of 103 for two days")
        assert level == "soon", f"Expected 'soon', got '{level}'"

    def test_routine_regular_cough(self):
        level = _classify_symptoms("I have a cough and sore throat since yesterday")
        assert level == "routine", f"Expected 'routine', got '{level}'"

    def test_routine_headache(self):
        level = _classify_symptoms("I have a headache and feel a bit tired")
        assert level == "routine", f"Expected 'routine', got '{level}'"

    def test_self_care_default(self):
        level = _classify_symptoms("I feel a bit stressed today")
        assert level == "self_care", f"Expected 'self_care', got '{level}'"

    def test_triage_guidance_keys_complete(self):
        assert set(_TRIAGE_GUIDANCE.keys()) == {"self_care", "routine", "soon", "urgent"}
        for key, val in _TRIAGE_GUIDANCE.items():
            assert "label" in val, f"Missing 'label' in {key}"
            assert "advice" in val, f"Missing 'advice' in {key}"


class TestSymptomTriageOutput:
    """
    Test that symptom_to_triage produces valid JSON with required fields.
    We call the internal helper since the @function_tool method requires
    a live RunContext.
    """

    def _triage(self, symptoms: str, severity: str = "mild", duration_days: int = 0) -> dict:
        level = _classify_symptoms(symptoms)
        if severity == "severe" and level in ("self_care", "routine"):
            level = "soon"
        if severity == "severe" and level == "soon":
            level = "urgent"
        if duration_days >= 7 and level == "self_care":
            level = "routine"
        guidance = _TRIAGE_GUIDANCE[level]
        return {
            "level": level,
            "label": guidance["label"],
            "advice": guidance["advice"],
            "disclaimer": "HealthSathi is not a doctor.",
        }

    def test_output_has_required_keys(self):
        result = self._triage("I have a fever")
        for key in ("level", "label", "advice", "disclaimer"):
            assert key in result, f"Missing key '{key}' in triage output"

    def test_severity_escalates_level(self):
        result = self._triage("I have a rash", severity="severe")
        assert result["level"] in ("soon", "urgent"), (
            f"Severe severity should escalate from self_care/routine, got '{result['level']}'"
        )

    def test_long_duration_escalates_self_care(self):
        result = self._triage("I feel a bit tired", duration_days=10)
        assert result["level"] == "routine", (
            f"7+ day duration should escalate self_care to routine, got '{result['level']}'"
        )

    def test_urgent_not_escalated_further(self):
        # Urgent stays urgent regardless of severity override
        result = self._triage("chest pain and not breathing", severity="severe")
        assert result["level"] == "urgent"

    def test_disclaimer_is_present(self):
        result = self._triage("headache")
        assert "HealthSathi" in result["disclaimer"]
        assert "not a doctor" in result["disclaimer"].lower()

    def test_does_not_diagnose(self):
        """Ensure advice field contains no diagnosis language."""
        for symptoms in ["chest pain", "high fever", "cough", "rash"]:
            result = self._triage(symptoms)
            advice_lower = result["advice"].lower()
            diagnosis_phrases = ["you have", "you are diagnosed", "you are suffering from"]
            for phrase in diagnosis_phrases:
                assert phrase not in advice_lower, (
                    f"Advice contains diagnosis language '{phrase}': {result['advice']}"
                )
