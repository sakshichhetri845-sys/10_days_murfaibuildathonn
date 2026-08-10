# Day 4 — Persistent Memory & RAG (#VoiceForBharat Challenge)

## Progress & Milestones Achieved
- [x] Implemented disk-backed memory storage using SQLite (`bolbuddy_memory.db` & [backend/src/db.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/db.py)).
- [x] Built structured memory tool functions (`save_user_memory`, `lookup_user_memory`, `forget_my_data`, `what_do_you_remember`).
- [x] Created zero-latency memory pre-fetching ([backend/src/async_memory.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/async_memory.py)) on user connection.
- [x] Implemented explicit verbal confirmation safeguards before memory deletion (`"Should I forget your saved learning details?"`).
- [x] Added RAG resource lookup ([backend/src/rag.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/rag.py)) for retrieving grammar and viva study tips.
- [x] Built comprehensive Pytest evaluation test suite for memory persistence across backend restarts.

---

## Overview
Day 4 equipped **BolBuddy** with long-term persistent memory and Retrieval-Augmented Generation (RAG). BolBuddy remembers learner profiles, names, learning goals, and topics practiced across separate session calls while maintaining strict user consent and deletion safety controls.

---

## Objective
Implement disk persistence, memory management functions, consent safeguards, and RAG capabilities as part of Day 4 of the #VoiceForBharat challenge.

---

## Memory & RAG Architecture

```
User Connection (WebRTC Room Join)
       ↓
Async Memory Pre-Fetch (async_memory.py)
       ↓
SQLite Database (bolbuddy_memory.db) → User Profile (Name, Level, Goals, Challenges)
       ↓
Function Tools:
  - save_user_memory (Consensual memory saving)
  - lookup_user_memory (Context retrieval on return)
  - forget_my_data (Verbal confirmation -> Record deletion)
  - search_learning_resources (RAG study tip retrieval)
```

---

## User Experience
1. **First Session**: User says *"My name is Sakshyam and I want to practice for internship interviews."*
   BolBuddy saves memory: *"Got it, I'll remember that."*
2. **Second Session**: User reconnects and says *"Hi BolBuddy!"*
   BolBuddy recalls profile: *"Welcome back Sakshyam! Ready to practice your internship interview skills?"*
3. **Data Deletion**: User says *"Forget my information."*
   BolBuddy asks confirmation: *"Should I forget your saved learning details?"*
   User confirms: *"Yes."* $\rightarrow$ BolBuddy deletes memory: *"Done. I've forgotten your saved learning details."*

---

## Tech Stack
- **Database**: SQLite3 (`backend/data/bolbuddy_memory.db`)
- **Voice AI Framework**: LiveKit Agents SDK (`@function_tool`)
- **Testing**: Pytest LLM-as-Judge Evaluation Framework

---

## Status
**Day 4 Completed.**
