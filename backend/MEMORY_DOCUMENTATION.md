# BolBuddy Persistent Memory Documentation (Day 4 Complete with RAG & Inspection)

This document describes the persistent SQLite database architecture, user identity resolution, learning memory model, agent function tools, explicit user consent rules, multilingual memory behavior, non-blocking asynchronous memory retrieval, **Forget Me** data deletion, **Memory Inspection** (`what_do_you_remember`), and the **Lightweight RAG System** for the **BolBuddy Voice Agent**.

---

## 1. User-Controlled Memory Inspection (`what_do_you_remember`)

- **Agent Tool (`what_do_you_remember`)**: Allows the user to inspect what BolBuddy currently remembers about them (*"What do you remember about me?"*, *"What have you saved about me?"*, *"Do you remember my goal?"*).
- **Voice-Friendly Natural Summaries**: Explains remembered facts warmly and concisely without technical database jargon, SQL terms, or internal IDs (e.g. *"I remember your name is Ramesh, you're practicing English for job interviews, and we've worked on self-introductions before!"*).
- **Mandatory Deletion Offer**: Every memory inspection summary warmly closes with an offer to forget: *"If you'd ever like me to forget any of that, just let me know!"*.
- **Empty & Deleted Memory**: If no memory exists or if data was deleted, explains warmly: *"I don't have any saved learning details about you yet, but I'd love to help you practice!"*.

---

## 2. Lightweight RAG System (`src/rag.py` & `backend/knowledge/`)

- **Curated Knowledge Base**: Markdown documents in `backend/knowledge/` tailored for Indian learners:
  - `beginner_grammar.md` (Indian English grammar tips, self-introductions, prepositions).
  - `everyday_english.md` (Daily situations, auto/cab travel, ordering food, market shopping).
  - `interview_english.md` (Internship & job interview prep, STAR method, self-introductions).
  - `viva_english.md` (College viva, project defense, asking clarification from professors).
  - `college_english.md` (College presentations, seminar GDs, emailing professors).
  - `pronunciation_tips.md` (V vs W, P vs F, TH sounds, overcoming MTI anxiety).
- **TF-IDF & Title Alignment Engine (`query_learning_resources`)**: Zero-dependency similarity search with title keyword alignment and stop-word filtering.
- **Agent Tool (`search_learning_resources`)**: Invoked ONLY when conceptual English learning or speaking tips are requested.
- **Voice Synthesis Rules**: Synthesizes retrieved concepts into warm spoken explanations. NEVER says *"According to the knowledge base..."* or reads markdown verbatim.
- **Fallbacks**: If no relevant document matches, returns `"No relevant learning resource found."` without fabricating answers.

---

## 3. "Forget Me" & Data Deletion (`src/memory_tools.py` & `src/prompts/memory.py`)

- **Agent Tool (`forget_my_data`)**: Permanently deletes the user's record from SQLite (`delete_user(user_id)`) and clears the in-memory cache (`clear_memory_cache(user_id)`).
- **Mandatory Confirmation**: Asks explicit verbal permission before deleting (*"I can remove your saved learning information. Would you like me to do that?"*). Once confirmed, states: *"Done. I've removed your saved learning information."*.

---

## 4. Asynchronous Non-Blocking Memory Retrieval (`src/memory_tools.py` & `src/agent.py`)

- **Identity Resolution**: Extracted upon WebRTC room connection (`await ctx.connect()`).
- **Background Execution (`asyncio.create_task` & `asyncio.to_thread`)**: Offloads SQLite disk I/O to background threads. The main event loop driving audio streaming, VAD, STT, and TTS is NEVER blocked.
- **In-Memory Cache (`_USER_MEMORY_CACHE`)**: Caches profile records for **< 1 millisecond** tool lookups.

---

## 5. Explicit User Consent Rules (`src/prompts/memory.py` & `src/memory_tools.py`)

- **Hard Constraint**: *"Never persist user information without explicit consent. If the user declines or does not clearly consent, do not save it."*
- **Ask Before Saving**: Explains what fact it wants to store and asks permission before calling `save_user_memory()`.

---

## 6. Multilingual & Code-Mixed Memory Normalization

- **Language-Neutral Storage**: Normalizes extracted learning goals and challenges into language-neutral English terms regardless of whether input is English, Hindi, or Hinglish.
- **Register Mirroring**: Returning user greetings mirror the learner's current conversational register.

---

## 7. Storage Location & User Identity

- **Default Database Path**: `backend/data/bolbuddy_memory.db` (ignored in git).
- **Persistent Anonymous User ID**: Managed by `frontend/app/api/token/route.ts` via 1-year HTTP cookies (`bolbuddy_user_id`).

---

## 8. Database Schema

```sql
CREATE TABLE IF NOT EXISTS user_memory (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    language_preference TEXT,
    facts TEXT DEFAULT '{}',
    last_interaction TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 9. Resilience & Error Handling

- All DB & RAG calls catch exceptions gracefully and return clean status strings without exposing database details or crashing the agent.
