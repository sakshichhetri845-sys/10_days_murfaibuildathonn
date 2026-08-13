# HealthSathi Persistent Memory & Privacy Documentation

This document describes the persistent SQLite database architecture, non-sensitive user preference storage, function tools, explicit user consent rules, multilingual memory behavior, and RAG health resource retrieval for **HealthSathi**.

## Architecture & Data Flow

- **Default Database Path**: `backend/data/healthsathi_memory.db`
- **User Preference Memory**: Stores non-sensitive details (`name`, `language_preference`, `reminder_preference`, `contact_preference`, `interaction_preferences`).
- **Data Privacy**: Strictly forbids storing passwords, OTPs, PINs, bank details, or sensitive medical histories.
- **Function Tools**:
  - `save_user_memory`: Consensual preference saving.
  - `lookup_user_memory`: Recalls non-sensitive saved facts upon user return.
  - `forget_my_data`: Asks explicit confirmation before clearing memory.
  - `what_do_you_remember`: Summarizes saved facts warmly for the user.
