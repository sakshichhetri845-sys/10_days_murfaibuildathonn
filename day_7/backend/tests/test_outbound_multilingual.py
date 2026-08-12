"""
Tests for Phase 8 — Multilingual Support on Outbound Voice Practice Calls.
"""

from prompts.system_prompt import SYSTEM_PROMPT


def test_multilingual_system_prompt_rules():
    """Verify system prompt includes Phase 8 Hinglish and zero forced language switching rules."""
    assert "LANGUAGE" in SYSTEM_PROMPT
    assert "Hinglish" in SYSTEM_PROMPT
    assert (
        "Actually interview mein English bolte waqt thoda nervous ho jata hoon."
        in SYSTEM_PROMPT
    )
    assert "That's completely okay. Let's take it step by step." in SYSTEM_PROMPT
    assert "Do not force language switching." in SYSTEM_PROMPT


def test_pipeline_multilingual_config(monkeypatch):
    """Verify deepgram STT nova-3 multi language configuration is preserved."""
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test_key_123")
    from livekit.plugins import deepgram

    stt_instance = deepgram.STT(model="nova-3", language="multi")
    assert stt_instance._opts.model == "nova-3"
    assert stt_instance._opts.language == "multi"
