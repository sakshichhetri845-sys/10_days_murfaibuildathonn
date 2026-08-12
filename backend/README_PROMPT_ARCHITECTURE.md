# HealthSathi Voice Agent — Prompt Architecture Documentation

HealthSathi is a Voice-First Health Access Companion designed for real-time voice interaction powered by LiveKit Agents, Murf Falcon TTS (Anisha voice), Deepgram Nova-3 Multilingual STT, and LLM Engines (Google Gemini / NVIDIA / Groq / OpenRouter).

## Prompt Architecture

HealthSathi's system prompt is assembled from modular Python components in `backend/src/prompts/`:

1. **`IDENTITY`** (`prompts/identity.py`): Core companion persona (HealthSathi) and primary purpose (helping users understand health guidance, basic symptom triage, and finding nearby facilities).
2. **`GUARDRAILS`** (`prompts/guardrails.py`): Strictly forbids disease diagnosis, prescription recommendations, or claims of medical certainty. Enforces emergency red-flag redirection to 112.
3. **`SYSTEM_PROMPT`** (`prompts/system_prompt.py`): Combines identity, objectives, language guidelines, guardrails, and style into a single instruction set for the agent.
