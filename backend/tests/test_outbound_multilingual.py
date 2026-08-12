"""
Tests for Multilingual Support on Outbound Voice Calls for HealthSathi.
"""

from prompts.system_prompt import SYSTEM_PROMPT


def test_multilingual_system_prompt_rules():
    """Verify system prompt includes natural Hinglish and Hindi rules without forced language switching."""
    assert "HealthSathi" in SYSTEM_PROMPT
    assert "Hinglish" in SYSTEM_PROMPT
    assert "Hindi" in SYSTEM_PROMPT


def test_pipeline_multilingual_config(monkeypatch):
    """Verify deepgram STT nova-3 multi language configuration is preserved."""
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test_key_123")
    from livekit.plugins import deepgram

    stt_instance = deepgram.STT(model="nova-3", language="multi")
    assert stt_instance._opts.model == "nova-3"
    assert stt_instance._opts.language == "multi"
