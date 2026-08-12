# Day 5 — Real Health Tools & Triage (Health Access Track)

## Progress & Milestones Achieved
- [x] Implemented safe symptom-to-triage classification tool ([symptom_to_triage](file:///c:/Users/livel/Downloads/murffff/sakshi/backend/src/agent.py)) evaluating 4 urgency levels (`self_care`, `routine`, `soon`, `urgent`).
- [x] Implemented healthcare facility lookup tool ([find_nearby_facility](file:///c:/Users/livel/Downloads/murffff/sakshi/backend/src/agent.py)) recommending appropriate facilities (health post, PHC, clinic, hospital emergency) based on urgency and location.
- [x] Implemented RAG health guidance retrieval ([search_health_resources](file:///c:/Users/livel/Downloads/murffff/sakshi/backend/src/rag.py)) over curated health guidance markdown docs.
- [x] Enforced strict non-diagnostic policy (0 disease diagnosis, 0 medication prescription, 0 claim of medical certainty).
- [x] Completely removed legacy BolBuddy English scoring and lesson tools (`score_spoken_answer`, `fetch_next_exercise`).

---

## Overview
Day 5 equips **HealthSathi** with domain-specific health tools. Instead of relying on generic conversation, HealthSathi executes tools to classify symptom urgency, suggest appropriate local health facilities, and query verified health guidance resources.

---

## What HealthSathi Uses

### 1. Symptom Triage Classifier (`symptom_to_triage`)
- **Purpose**: Classifies user-reported symptoms into a safe triage level.
- **Urgency Levels**:
  - `self_care` (ROUTINE / LOW): Minor, stable symptoms managed at home with rest/fluids.
  - `routine` (MODERATE): Non-urgent symptoms suitable for a local health post or PHC visit.
  - `soon` (PROMPT / HIGH): Symptoms requiring evaluation at a clinic/PHC within 24–48 hours.
  - `urgent` (EMERGENCY): Red-flag symptoms (chest pain, severe breathing difficulty, stroke) requiring immediate emergency hospital care or **112**.
- **Rules**: Never diagnoses medical conditions, never prescribes drugs.

### 2. Healthcare Facility Lookup (`find_nearby_facility`)
- **Purpose**: Returns recommendations on the type of facility to visit based on urgency and user location.
- **Facility Types**: Health post / community pharmacy (`self_care`), PHC / community clinic (`routine`), District hospital (`soon`), Emergency department (`urgent`).
- **Location**: Uses user-provided location (e.g. Kathmandu, Ward 3) or asks for city/area if unknown.

### 3. Health Information Retrieval (`search_health_resources`)
- **Purpose**: Zero-dependency RAG module querying verified markdown documents in `backend/knowledge/` (`symptom_basics.md`, `doctor_visit_prep.md`, `urgent_care_guidance.md`).

---

## Tool Flow

```
User (Spoken Speech)
       ↓
Speech-to-Text (Deepgram Nova-3)
       ↓
LLM Pipeline (Gemini / NVIDIA / Groq / OpenRouter)
       ↓
Structured Function Call (symptom_to_triage / find_nearby_facility / search_health_resources)
       ↓
Tool Execution (Silent execution, returns structured JSON metadata)
       ↓
Voice Response Generation (Concise, empathetic, non-diagnostic guidance)
       ↓
Text-to-Speech (Murf Falcon Audio Synthesis, voice="Anisha")
```

---

## Example

### Symptom Triage & Facility Lookup
- **User Input**: *"I have a mild cough and sore throat in Kathmandu."*
- **Tool Execution**: `symptom_to_triage(symptoms="mild cough and sore throat")` $\rightarrow$ `level: "routine"`.
- **Tool Execution**: `find_nearby_facility(location="Kathmandu", urgency="routine")` $\rightarrow$ `PHC or community clinic`.
- **HealthSathi Response**: *"A mild cough and sore throat are common. You can visit a local primary health centre or clinic in Kathmandu for a check-up. If symptoms worsen, please consult a doctor."*

---

## Status
**Day 5 Completed — Real Health Tools & Triage Active.**
