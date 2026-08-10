# Day 4 — Persistent Memory & RAG

## Overview
Day 4 equipped **BolBuddy** with persistent memory and Retrieval-Augmented Generation (RAG), allowing the voice agent to remember learner profiles, names, goals, and topics across sessions while providing consent-based data management.

## Objective
Implement disk-backed memory storage (SQLite), memory tool functions (`save_user_memory`, `lookup_user_memory`, `forget_my_data`), and explicit verbal confirmation before memory deletion.

## What I Built
- SQLite Database Layer ([backend/src/db.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/db.py)) storing user facts, learning goals, and practice history.
- Memory Function Tools ([backend/src/memory_tools.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/memory_tools.py)).
- Automatic Memory Pre-fetching ([backend/src/async_memory.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/async_memory.py)) for zero-latency session starts.
- Consent & Confirmation Safeguards: BolBuddy explicitly asks for verbal confirmation before deleting memory via `forget_my_data`.
- RAG Resource Matcher ([backend/src/rag.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/rag.py)) for retrieving grammar and viva study tips.

## Implementation
- Disk database: `backend/data/bolbuddy_memory.db`.
- Async pre-fetch on room join in `backend/src/agent.py`.
- Comprehensive test coverage in `backend/tests/test_memory_db.py`, `test_memory_tools.py`, `test_forget_me.py`, and `test_multilingual_memory.py`.

## User Experience
Returning users are greeted by name and remembered for their specific practice goal (e.g. *"Welcome back Sakshyam! Ready to practice for your internship interview today?"*).

## Key Features
- Disk persistence across backend restarts.
- Consent-based data saving (`"Got it, I'll remember that."`).
- Explicit verbal confirmation before deletion (`"Should I forget your saved learning details?"`).

## Demo Flow
1. User: *"My name is Ramesh and I am preparing for an internship interview."*
2. BolBuddy: *"Got it, I'll remember that."*
3. User reconnects later: *"Hi BolBuddy!"*
4. BolBuddy: *"Welcome back Ramesh! Ready to practice your internship interview skills?"*

## Tech Used
- Python 3.10+ & SQLite3
- LiveKit Agents `@function_tool`
- Pytest LLM-as-Judge Evaluation Suite

## Files / Components
- `backend/src/db.py`
- `backend/src/memory_tools.py`
- `backend/src/async_memory.py`

## Status
**Completed.**
