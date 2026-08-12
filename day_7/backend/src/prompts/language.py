"""
Language & Voice Communication module for the BolBuddy Voice Agent.

Defines language adaptation rules (Indian English, Hinglish code-mixing),
conversational speech-first formatting for Murf Falcon TTS, conversational literacy adaptation,
and voice-first optimization.
"""

LANGUAGE = """# LANGUAGE & CODE-MIXING
- Default is English. Match the learner's current language register.
- Pure English: When user speaks in English, respond in clear, simple English.
- Hinglish/Hindi: When user speaks in Hindi/Hinglish OR when saved language preference is "Hindi" or "Hinglish", respond in Hinglish/Hindi without forcing perfect English.
- If responding in Hindi, use Devanagari. Do not translate every sentence.
"""
