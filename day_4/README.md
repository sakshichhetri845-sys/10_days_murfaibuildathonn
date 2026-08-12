# Day 4 — Persistent Memory & Privacy (Health Access Track)

## Progress & Milestones Achieved
- [x] Implemented disk-backed memory storage using SQLite (`healthsathi_memory.db` & [backend/src/db.py](file:///c:/Users/livel/Downloads/murffff/sakshi/backend/src/db.py)).
- [x] Built structured memory tool functions (`save_user_memory`, `lookup_user_memory`, `forget_my_data`, `what_do_you_remember`).
- [x] Created zero-latency memory pre-fetching ([backend/src/memory_tools.py](file:///c:/Users/livel/Downloads/murffff/sakshi/backend/src/memory_tools.py)) on user connection.
- [x] Implemented explicit verbal confirmation safeguards before memory deletion.
- [x] Added RAG resource lookup ([backend/src/rag.py](file:///c:/Users/livel/Downloads/murffff/sakshi/backend/src/rag.py)) for retrieving health guidance documents.
- [x] Strictly removed legacy BolBuddy learning fields (speaking scores, vocabulary mistakes, learning goals).

---

## Overview
Day 4 equipped **HealthSathi** with non-sensitive persistent memory and Retrieval-Augmented Generation (RAG). HealthSathi remembers non-sensitive user preferences (`name`, `language_preference`, `reminder_preference`, `contact_preference`) across calls while respecting strict privacy rules.

---

## Objective
Implement disk persistence, non-sensitive memory tools, consent safeguards, and RAG health resource retrieval as part of Day 4 of the #VoiceForBharat Health Access challenge.

---

## Privacy & Memory Architecture

```
User Connection (WebRTC Room Join)
       ↓
Async Memory Pre-Fetch (memory_tools.py)
       ↓
SQLite Database (healthsathi_memory.db) → Health Profile (Name, Language, Reminder, Contact)
       ↓
Function Tools:
  - save_user_memory (Consensual non-sensitive memory saving)
  - lookup_user_memory (Context retrieval on return)
  - forget_my_data (Verbal confirmation -> Record deletion)
  - search_health_resources (RAG health guidance retrieval)
```

> [!CAUTION]
> **Data Privacy Policy**: HealthSathi does NOT store passwords, OTPs, PINs, bank details, or sensitive medical histories.

---

## User Experience
1. **First Session**: User says *"My name is Ramesh and I prefer updates in Hindi."*
   HealthSathi saves preference: *"Dhanyavaad Ramesh, maine aapka preference save kar liya hai."*
2. **Second Session**: User reconnects and says *"Hello HealthSathi!"*
   HealthSathi recalls profile: *"Welcome back Ramesh! How can I help with your health today?"*
3. **Data Deletion**: User says *"Forget my saved details."*
   HealthSathi asks confirmation: *"Are you sure you want me to delete your saved profile?"*
   User confirms: *"Yes."* $\rightarrow$ HealthSathi clears memory: *"Saved memory deleted successfully."*

---

## Status
**Day 4 Completed — HealthSathi Memory & Privacy Active.**
