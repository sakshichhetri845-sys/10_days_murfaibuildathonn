# BolBuddy Voice Agent — Prompt Architecture Documentation

## Overview

BolBuddy is an AI English Speaking & Literacy Companion designed for real-time voice interaction powered by LiveKit Agents, Murf Falcon TTS, Deepgram STT, and Groq LLM (`llama-3.1-8b-instant`).

To keep single-turn request context token-efficient (~550-600 tokens total) and stay strictly under Groq's 6,000 TPM limit, the prompt is structured into modular constants combined in a clean priority sequence.

## Prompt Module Hierarchy

The system prompt (`SYSTEM_PROMPT`) is composed in `backend/src/prompts/system_prompt.py` in the following exact sequence:

1. **`IDENTITY`** (`prompts/identity.py`): Core companion persona (BolBuddy) and primary purpose (building spoken English confidence).
2. **`GUARDRAILS`** (`prompts/guardrails.py`): Safety boundaries, refusal rules, no PII access, no tool leakage in audio, and TTS formatting rules (no markdown/emojis).
3. **`OBJECTIVES`** (`prompts/objectives.py`): Conversational goals, warm encouragement, and interview/viva practice invitations.
4. **`KNOWLEDGE`** (`prompts/knowledge.py`): RAG usage rules (`search_learning_resources`) and audio delivery guidelines (never cite doc names).
5. **`MEMORY_INSTRUCTIONS`** (`prompts/memory.py`): Rules for `lookup_user_memory`, `save_user_memory`, explicit verbal confirmation for `forget_my_data`, and memory privacy offers.
6. **`LANGUAGE`** (`prompts/language.py`): Language adaptation rules (Hinglish mirroring when user speaks Hindi/Hinglish) and daily practice topic suggestions.
7. **`STYLE`** (`prompts/style.py`): Tone of voice (warm, patient), strict rule against correcting speech/grammar mistakes, and brevity (1-3 short sentences).
8. **`GREETING`** (`prompts/greeting.py`): Persona greeting guidelines for new vs returning users.
9. **`CONVERSATION_PRINCIPLES`** (`prompts/conversation_principles.py`): Single-question turn-taking and empathetic listening principles.

## Token Optimization Architecture

- **System Prompt**: Streamlined to ~420 tokens (reduced from ~640 tokens).
- **Function Tool Schemas**: Concise docstrings reduce schema overhead to ~110 tokens (reduced from ~400 tokens).
- **Initial Greeting**: Direct audio synthesis via `session.say(...)` avoids wasting an initial LLM generation turn on room join (saves ~1,300 startup tokens).
- **History Pruning**: Dynamic pruning limits active conversation history to 4 messages (~80-120 tokens).
- **Total Request Context per Turn**: ~550-600 tokens (down from ~1,803 tokens).
