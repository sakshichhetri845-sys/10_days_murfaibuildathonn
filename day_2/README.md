# Day 2 — Personality & Safety Guardrails (#VoiceForBharat Challenge)

## Progress & Milestones Achieved
- [x] Designed the core **BolBuddy** persona: a warm, encouraging English practice companion for Indian learners.
- [x] Built a modular System Prompt architecture ([backend/src/prompts/](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/prompts/)).
- [x] Implemented ultra-concise response style rules (1–2 short sentences, < 20 words per reply).
- [x] Added support for code-mixed speech (Hinglish/Hindi register matching).
- [x] Integrated safety guardrails preventing out-of-scope roleplay, examiner persona overload, and technical jargon leakage.

---

## Overview
Day 2 focused on giving **BolBuddy** a distinct personality tailored for Indian students preparing for job interviews, college vivas, campus presentations, and everyday English speech. Rather than sounding like a strict examiner or generic assistant, BolBuddy speaks like a warm, supportive peer.

---

## Objective
Establish a custom system prompt, conversation principles, Indian context safety guardrails, and token-efficient response guidelines as part of Day 2 of the #VoiceForBharat challenge.

---

## BolBuddy Persona Architecture

### 1. Identity (`identity.py`)
- Empathetic, friendly companion for Indian engineering students and job aspirants.
- Encourages practice without shaming mistakes or giving long lectures.

### 2. Conversation Principles (`conversation_principles.py`)
- **Strict Brevity**: Normally answer in 1 sentence, maximum 2 short sentences (under 20 words).
- **Code-Mixing Support**: Understands Hinglish and responds in natural, accessible language.
- **Goal Offering**: Proactively offers practice options when learners mention interview or viva goals.

### 3. Safety & System Guardrails (`guardrails.py`)
- Refuses non-educational requests politely in one short sentence.
- Never outputs raw tool syntax (`<function=...>`, JSON objects) or internal database terms.

---

## System Prompt Compilation

All prompt modules compile into a compact system prompt (~340 tokens) defined in [backend/src/prompts/system_prompt.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/prompts/system_prompt.py).

---

## User Experience
1. **User**: *"Hi BolBuddy, I feel nervous speaking English in job interviews."*
2. **BolBuddy**: *"That's a fantastic goal! I'd love to help you prepare. Want to practice common interview questions in English or Hinglish?"*

---

## Tech Stack
- **Voice AI Framework**: LiveKit Agents SDK (`livekit-agents`)
- **Prompt Architecture**: Modular Python Prompt Components
- **Language Support**: English, Hindi, Hinglish

---

## Status
**Day 2 Completed.**
