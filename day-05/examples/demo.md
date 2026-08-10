# Day 5 Demo Scenario: Tool Execution Flow

This document provides the exact demonstration script and execution trace for the **Day 5 — The Tools** milestone of BolBuddy (#VoiceForBharat).

---

## 🎤 Demonstration Script & Transcript

### Scene 1: Requesting a Practice Exercise
> **User**: "BolBuddy, I want to practice for an internship interview."
>
> **System Log**:
> `[TOOL CALL] fetch_next_exercise(level="intermediate", topic="internship interviews")`
> `[TOOL OUTPUT] {"id": "interview_01", "level": "intermediate", "topic": "internship interviews", "exercise": "Tell me about yourself in about 30 seconds."}`
>
> **BolBuddy (Spoken via Murf Falcon)**:
> *"Sure, Sakshyam. Let's practice your introduction. Tell me about yourself in about 30 seconds."*

---

### Scene 2: Spoken Answer Response
> **User**: "Hi, I'm Sakshyam. I'm currently studying engineering. I'm interested in technology and I want to gain practical experience through this internship."
>
> **System Log**:
> `[STT Output] Speech transcribed by Deepgram Nova-3`
>
> **BolBuddy (Spoken via Murf Falcon)**:
> *"Nice job! Your introduction is clear and easy to follow. Would you like me to evaluate your answer?"*

---

### Scene 3: Requesting Spoken Answer Evaluation
> **User**: "Yes, how did I do?"
>
> **System Log**:
> `[TOOL CALL] score_spoken_answer(question="Tell me about yourself in about 30 seconds.", answer="...", practice_topic="interview")`
> `[TOOL OUTPUT] {"score": 7, "strength": "Clear and relevant introduction", "improvement": "Add 1 sentence about your specific project background"}`
>
> **BolBuddy (Spoken via Murf Falcon)**:
> *"That's 7 out of 10. Your ideas were clear and easy to understand. One thing to improve is mentioning a specific project background."*

---

## 🛠️ Tool Execution Characteristics
- **Zero Raw Syntax Leakage**: Function calls (`<function=...>`, JSON strings) are handled strictly internally.
- **Silent Tool Calls**: The user hears only the final natural spoken response.
- **Single Generation Per Turn**: Each user speech input triggers exactly ONE LLM generation and ONE spoken TTS output.
