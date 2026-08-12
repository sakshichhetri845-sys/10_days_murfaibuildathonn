# Day 2 — Personality & Safety Guardrails (Health Access Track)

## Progress & Milestones Achieved
- [x] Designed the core **HealthSathi** persona: a calm, empathetic, voice-first health access companion.
- [x] Built a modular System Prompt architecture ([backend/src/prompts/](file:///c:/Users/livel/Downloads/murffff/sakshi/backend/src/prompts/)).
- [x] Implemented concise, voice-first response style rules (1–2 short sentences per turn, one question at a time).
- [x] Added support for code-mixed speech (Hinglish/Hindi register matching).
- [x] Integrated non-diagnostic safety guardrails preventing disease diagnosis, prescription recommendations, or claims of medical certainty.

---

## Overview
Day 2 focused on giving **HealthSathi** a distinct personality tailored for everyday health guidance. Rather than sounding like a medical diagnostic engine or doctor, HealthSathi speaks like a warm, supportive health access companion.

---

## Objective
Establish a custom system prompt, non-diagnostic guardrails, emergency red-flag handling, and token-efficient response guidelines as part of Day 2 of the #VoiceForBharat Health Access challenge.

---

## HealthSathi Persona Architecture

### 1. Identity (`identity.py`)
- Empathetic, calm health access companion.
- Helps users describe symptoms naturally and understand general next steps without diagnosing diseases.

### 2. Conversation Principles (`conversation_principles.py`)
- **Voice-First Brevity**: Answer in 1–2 short sentences per turn; ask one question at a time.
- **Code-Mixing Support**: Understands English, Hindi, and Hinglish.
- **Safety First**: Prioritizes emergency warning signs over casual conversation.

### 3. Non-Diagnostic Guardrails (`guardrails.py`)
- **Never Diagnoses**: Replaces "You have X" with safe urgency level guidance.
- **Never Prescribes**: Refuses prescription medication or dosage advice.
- **Emergency Priority**: Directs severe symptoms (chest pain, stroke, breathing difficulty) to emergency services (**112**) or hospital.
- **Consent Rule**: Requires explicit user consent before calling `create_escalation` or `save_user_memory`.

---

## System Prompt Compilation

All prompt modules compile into a compact system prompt assembled in [backend/src/prompts/system_prompt.py](file:///c:/Users/livel/Downloads/murffff/sakshi/backend/src/prompts/system_prompt.py).

---

## User Experience
1. **User**: *"Mujhe kal se fever ho raha hai, kya karna chahiye?"*
2. **HealthSathi**: *"Aapko sunkar afsoos hua. Agar fever ke saath saans lene mein takleef ya tez dard hai to turant doctor ko dikhayein. Kya aapko koi aur symptom bhi hai?"*

---

## Status
**Day 2 Completed — HealthSathi Persona & Guardrails Active.**
