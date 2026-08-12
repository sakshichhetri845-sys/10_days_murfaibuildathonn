# Day 7 Progress Snapshot – BolBuddy AI Voice Companion

This directory (`day_7/`) contains the **complete codebase, tests, and documentation snapshot** for **BolBuddy** as built through Day 7.

---

## 🎯 Day 7 Focus: Know When to Ask for Human Help (Human Escalation & Discord Channel)

Day 7 introduces **Human Help & Escalation Protocols** to **BolBuddy**, enabling the voice agent to recognize when a learner requires real human assistance, ask explicit permission, create an encrypted/sanitized support ticket, notify the human support team via a **Discord Webhook channel**, and display ticket status in the **Human Help UI Dashboard**.

---

## 🚀 All Features Included in Day 7 Snapshot

- 🎙️ **Day 1 & 2**: Real-time duplex audio streaming using LiveKit Agents SDK, Deepgram Nova-3 Multilingual STT, Murf Falcon TTS (Anisha voice, 55ms latency), and BolBuddy Indian English persona.
- 💬 **Day 3**: Next.js 15 web interface with animated voice orb visualizer, mic controls, and live conversation transcript view.
- 🧠 **Day 4**: Persistent user memory (`bolbuddy_memory.db`), consent-based memory saving, verbal confirmation before memory deletion, and RAG resource search.
- 📊 **Day 5**: Function tools (`fetch_next_exercise` & `score_spoken_answer`), curated exercise dataset, single-turn LLM response, zero tool syntax leakage, and multi-tier LLM failover.
- 📞 **Day 6**: Scheduled outbound practice calls via Linphone SIP trunk (`OUTBOUND_CALL_ENABLED`), state machine, 3-part opening, and short spoken practice.
- 🚨 **Day 7**: Learner distress & teacher request detection, 7-step consent protocol, Discord Webhook channel delivery (`DISCORD_ESCALATION_WEBHOOK_URL`), PII scrubbing, and internal Human Help dashboard UI.

---

## 🏗 Day 7 Human Escalation Flow

```text
Learner (Voice Session)
  ↓
BolBuddy detects Distress or Teacher Request
  ↓
BolBuddy asks explicit permission ("Is that okay?")
  ↓
Learner says "Yes"
  ↓
create_escalation()
  ↓
1. Sanitize PII (Passwords, OTPs, PINs, Bank Details)
2. Save to SQLite database (bolbuddy_memory.db) → Status: OPEN
3. POST payload to DISCORD_ESCALATION_WEBHOOK_URL
4. Display ticket card on Frontend UI (ESC-XXXX)
  ↓
Learner receives spoken confirmation:
"Your support request has been initialized. Your reference ID is ESC-XXXX. A human teacher will review your request and contact you within 24 hours."
```

---

## 📁 Day 7 Snapshot Directory Structure

```text
day_7/
├── backend/
│   ├── src/
│   │   ├── agent.py            # Main voice engine entrypoint & tool definitions
│   │   ├── escalation_tools.py # Human escalation, PII scrubbing, Discord webhook
│   │   ├── db.py               # SQLite database schema (memory & escalations)
│   │   ├── memory_tools.py     # User context memory & consent handlers
│   │   ├── outbound_agent.py   # Outbound telephony SIP call agent
│   │   └── prompts/            # System prompts & persona definitions
│   ├── tests/                  # 133 automated pytest unit & LLM evaluation tests
│   ├── pyproject.toml          # Python dependencies (uv)
│   └── verify_day7_scenarios.py# Verification script for Day 7 test scenarios
├── frontend/
│   ├── app/                    # Next.js pages & API routes (/api/token, /api/escalations)
│   ├── components/             # React UI components (bolbuddy-session-view, escalations-drawer)
│   ├── hooks/                  # Audio visualizer & state hooks
│   ├── lib/                    # Utilities & styling helpers
│   ├── styles/                 # CSS globals
│   ├── app-config.ts           # Branding & accent colors
│   └── package.json            # Node dependencies (pnpm)
├── start_app.ps1               # All-in-one Windows launcher script
├── start_app.sh                # All-in-one Linux/macOS launcher script
└── README.md                   # This snapshot documentation file
```

---

## 🧪 Test Suite Verification

```bash
cd backend
uv run pytest
```

```text
============================= test session starts =============================
collected 133 items

test_keys.py ...                                                         [  2%]
tests/test_agent.py .....                                                [  6%]
tests/test_async_memory.py .....                                         [  9%]
tests/test_call_outcomes.py .........                                    [ 16%]
tests/test_consent.py ......                                             [ 21%]
tests/test_day4_two_calls.py .                                           [ 21%]
tests/test_escalation.py ........                                        [ 27%]
tests/test_exercise_tool.py .......                                      [ 33%]
tests/test_final_integration.py ..                                       [ 34%]
...
=========================== 133 passed in 167.32s ===========================
```
