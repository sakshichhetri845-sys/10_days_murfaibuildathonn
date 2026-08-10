# Day 5 — The Tools (#VoiceForBharat Challenge)

## Progress & Milestones Achieved
- [x] Implemented domain exercise retrieval tool (`fetch_next_exercise`) with category subtopic rotation.
- [x] Implemented spoken answer evaluation tool (`score_spoken_answer`) providing structured clarity, grammar, and fluency feedback.
- [x] Curated a local exercise dataset ([day_5/tools/exercise_data.json](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/day_5/tools/exercise_data.json)) covering 6 topic domains and 3 difficulty tiers.
- [x] Implemented a **Multi-Tier LLM Architecture**: Primary (NVIDIA API `z-ai/glm-5.2`), Secondary (Groq Multi-Key Pool `llama-3.1-8b-instant`), Tertiary (Google Gemini `gemini-2.0-flash`).
- [x] Enforced single-turn LLM generation and silent tool calls (0 XML/JSON tool syntax leakage to user, transcript, or Murf TTS).
- [x] Verified full backend test suite (**76 / 76 tests passed**).

---

## Overview
Day 5 empowers **BolBuddy** with real structured tools. Instead of relying solely on static conversation generation, BolBuddy can now execute functions dynamically to fetch domain-specific speaking exercises and evaluate completed spoken answers with structured numerical and qualitative feedback.

---

## Objective
The official **Day 5 — Learning & Literacy** challenge requirement is to build structured function calls that fetch or compute domain data, enabling the voice agent to serve as a practical learning companion.

---

## What I Built

### 1. Exercise Retrieval (`fetch_next_exercise`)
- Dynamically selects speaking exercises tailored to the learner's level (`beginner`, `intermediate`, `advanced`) and target topic (interviews, viva, presentations, everyday speech, workplace communication).
- Uses category-based subtopic rotation so learners receive fresh practice questions when requesting multiple exercises in the same session.
- Production source code: [backend/src/exercises.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/exercises.py).
- Standalone tool reference: [day_5/tools/exercise_tool.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/day_5/tools/exercise_tool.py).

### 2. Spoken Answer Scoring (`score_spoken_answer`)
- Evaluates the user's transcribed spoken answer after STT completion across clarity, sentence structure, filler word ratio, and grammar accuracy.
- Returns a structured dictionary containing a score (1–10), key strength, and actionable feedback.
- Production source code: [backend/src/scoring.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/scoring.py).
- Standalone tool reference: [day_5/tools/answer_scoring.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/day_5/tools/answer_scoring.py).

---

## Data Source
- **Dataset Type**: Curated local dataset ([day_5/tools/exercise_data.json](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/day_5/tools/exercise_data.json)).
- **Why Selected**: Ensures zero-latency retrieval, offline predictability, and targeted relevance for Indian engineering students and job aspirants.
- **Live vs Local**: BolBuddy currently uses a curated local exercise dataset for Day 5. No external exercise API is required for this milestone.
- **Data Freshness**: Versioned with the Day 5 project and updated whenever exercise categories or difficulty tiers are expanded.

---

## Tool Flow

```
User (Spoken Speech)
       ↓
Speech-to-Text (Deepgram Nova-3)
       ↓
LLM Pipeline (NVIDIA API Primary → Groq Multi-Key Pool Secondary)
       ↓
Structured Function Call (fetch_next_exercise / score_spoken_answer)
       ↓
Tool Execution (Silent execution, returns compact JSON metadata)
       ↓
Single Natural Response Generation (Under 20 words, 0 XML/JSON leakage)
       ↓
Text-to-Speech (Murf Falcon Audio Synthesis)
```

---

## Example

### Exercise Selection
- **User Input**: `"Give me an intermediate interview exercise."`
- **Tool Execution**: `fetch_next_exercise(level="intermediate", topic="interview")`
- **BolBuddy Response**: *"Tell me about a challenge you faced during a project and how you handled it."*

### Spoken Answer Scoring
- **User Input**: `"How did I do?"`
- **Tool Execution**: `score_spoken_answer(question="...", answer="...", practice_topic="interview")`
- **BolBuddy Response**: *"That's 7 out of 10. Your ideas were clear and easy to follow. One thing to improve is making your phrasing more natural."*

---

## Failure Handling
- If `fetch_next_exercise` fails or finds no match, BolBuddy executes a clean fallback:
  *"I couldn't load a practice question right now, but we can still practice. Tell me about yourself."*
- If `score_spoken_answer` fails:
  *"I couldn't score that answer right now, but we can keep practicing."*
- Tool failures never output raw tracebacks, error codes, or invented data.

---

## Token Efficiency
- **Compact Tool Schemas**: Short docstrings (< 20 tokens per tool definition).
- **Minimal Tool Payloads**: Returns only essential text fields, avoiding large JSON payloads.
- **Single Generation Per Turn**: Non-preemptive generation configuration prevents duplicate LLM turns and duplicate spoken responses.
- **Multi-Key & Multi-Tier Failover**: NVIDIA API primary with Groq multi-key fallback prevents 429 rate limit disruptions.

---

## Day 5 Requirements Checklist
- [x] Tool implemented (`fetch_next_exercise` & `score_spoken_answer`)
- [x] Real/curated domain data documented
- [x] Tool description defined
- [x] Failure path handled
- [x] Data source documented
- [x] Tool connected to BolBuddy
- [x] Natural spoken response
- [x] README completed

---

## Demo Scenario
See [day_5/examples/demo.md](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/day_5/examples/demo.md) for the complete video script and demonstration dialogue.

---

## Tech Used
- **Voice AI Framework**: LiveKit Agents SDK (`livekit-agents ~1.4`)
- **Speech-to-Text**: Deepgram Nova-3 (`language="multi"`)
- **Text-to-Speech**: Murf Falcon TTS (`voice="Anisha"`)
- **Primary LLM**: NVIDIA API (`model="z-ai/glm-5.2"`)
- **Secondary LLM**: Groq Multi-Key Pool (`model="llama-3.1-8b-instant"`)
- **Language**: Python 3.10+

---

## Status
**Day 5 Completed.**
