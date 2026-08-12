# README_PROMPT_ARCHITECTURE.md — HealthSathi Prompt System

## Prompt Architecture

HealthSathi's system prompt is intentionally divided into small, focused Python modules in `backend/src/prompts/` rather than one monolithic text file.

Each module has a single, clear responsibility. This makes the prompt easy to audit, test, and maintain across all 7 Days of Voice Agents requirements.

The complete system prompt is dynamically assembled in `backend/src/prompts/system_prompt.py`.

---

## Modular Architecture

### 1. `identity.py`
Defines who HealthSathi is: a friendly, voice-first health access companion. Establishes core purpose (helping users navigate non-emergency health questions) and explicitly states that HealthSathi is not a doctor.

### 2. `objectives.py`
Defines conversation goals: symptom-to-triage classification, facility guidance, medication reminder management, and human escalation when needed.

### 3. `knowledge.py`
Defines domain knowledge boundaries: general wellness, basic triage criteria, prep for doctor visits, emergency warning signs. Explicitly forbids inventing medical facts or claiming medical certainty.

### 4. `language.py`
Defines voice-first multilingual communication in English, Hindi, and Hinglish/code-mixed speech for natural Indian voice interactions.

### 5. `guardrails.py`
Defines non-negotiable safety rules:
- **No Medical Diagnosis**: Never say "You have [disease]".
- **No Prescriptions**: Never recommend prescription medications or dosages.
- **Emergency Priority**: Immediately direct red-flag symptoms (chest pain, breathing difficulty, stroke) to emergency services (**112**) or nearest hospital.
- **Explicit Consent**: Require user consent before calling `create_escalation` or `save_user_memory`.
- **Privacy Protection**: Never request or persist passwords, OTPs, PINs, or credit card numbers.

### 6. `style.py`
Defines conversational style: calm, empathetic, concise (1-2 sentences), non-judgmental, and one question at a time.

### 7. `greeting.py`
Defines warm initial greetings for new and returning users, framing HealthSathi as a helpful voice companion.

### 8. `conversation_principles.py` & `decision_hierarchy.py`
Guides response priorities: Safety & Emergency > Human Escalation > Triage & Guidance > Preference Saving.

---

## Key Safety Rules

1. **Non-Diagnostic Policy**: HealthSathi uses coarse triage levels (`self_care`, `routine`, `soon`, `urgent`) to suggest next steps without giving a formal medical diagnosis.
2. **Consent-First Escalation**: Human support requests (`create_escalation`) are only created after explaining what data is shared and obtaining explicit verbal consent ("Yes").
3. **Emergency Red-Flag Handling**: Severe symptoms bypass routine chit-chat to recommend urgent emergency evaluation.
