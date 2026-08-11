# Day 6 — Outbound Telephony & Sub-350ms Voice AI Integration

This directory contains the full Day 6 codebase for **BolBuddy Voice AI Agent**, featuring **Outbound SIP Telephony Practice Calls (Linphone integration)**, **Sub-350ms OpenRouter LLM Streaming**, **Murf Falcon TTS (Anisha voice)**, and **Deepgram Nova-3 Multilingual STT**.

---

## 🌟 Key Features Completed in Day 6

1. **Sub-350ms Voice Latency via OpenRouter**:
   - Primary LLM: `meta-llama/llama-3.1-8b-instruct` via OpenRouter endpoint (`https://openrouter.ai/api/v1`).
   - Fallback hierarchy: **OpenRouter → NVIDIA → Groq → Google Gemini**.
   - Disabled parallel tool calls (`parallel_tool_calls=False`) to avoid duplicate JSON payload issues.

2. **Multilingual Speech Recognition (`nova-3` `multi`)**:
   - Deepgram Nova-3 with `language="multi"` and `smart_format=True` for seamless transcription of English, Hindi, and Hinglish.

3. **Murf Falcon Ultra-Fast Audio Synthesis**:
   - Voice: `Anisha` (`style="Conversation"`), starting audio playback in ~100ms TTFB.
   - Includes sanitization via `_clean_tts_text()` to prevent XML tags, JSON markup, or raw function tags (`<function=...>`) from reaching speech audio.

4. **Frontend Schedule & Instant "Call Me Now" Buttons**:
   - [practice-call-section.tsx](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/day_6/frontend/components/app/practice-call-section.tsx): Learners can enter their phone number or Linphone ID (`sakshyambhttr`) and click **Schedule Daily Practice** or **Call Me Now**.

5. **LiveKit Agent Dispatch Architecture**:
   - Creates a LiveKit `CreateAgentDispatchRequest` (`agent_name="outbound-agent"`), ensuring LiveKit Cloud connects the dedicated telephony worker to dial the phone/SIP app and speak immediately upon answer.

6. **Clean Task Lifecycle & Asyncio Safety**:
   - Converted `session.start(...)` into a non-blocking task and awaited it at the end of the entrypoint, eliminating `Task was destroyed but it is pending` warnings.

7. **Single-Command Startup Script**:
   - Executing `.\start_app.ps1` (or `./start_app.sh`) starts the Web Agent, Outbound Telephony Agent, and Next.js Frontend UI simultaneously in separate windows.

---

## 📁 Repository Structure

```
day_6/
├── backend/
│   ├── src/
│   │   ├── agent.py                 # Web Browser Agent entrypoint
│   │   ├── telephony/outbound/agent.py # Dedicated Outbound Phone Call Agent
│   │   ├── telephony/outbound/dial.py  # Manual CLI Outbound Dispatcher
│   │   ├── outbound.py              # Outbound dispatch trigger & retry logic
│   │   ├── telephony.py             # LiveKit SIP configuration & requests
│   │   ├── db.py                    # SQLite database for persistence & scheduling
│   │   └── prompts/system_prompt.py # Production system prompt
│   └── tests/
│       ├── test_agent.py            # LLM-judged agent unit tests
│       └── test_telephony.py        # Outbound call unit tests
├── frontend/
│   ├── app/
│   │   ├── page.tsx                 # Main web voice practice app
│   │   └── api/outbound/practice/route.ts # Next.js API route for outbound calls
│   └── components/app/
│       └── practice-call-section.tsx # Daily Practice Schedule & Call Me Now UI
├── start_app.ps1                    # One-command startup script (Windows)
└── start_app.sh                     # One-command startup script (Linux/macOS)
```

---

## 🐞 Bugs Encountered & Exact Solutions

| # | Issue / Error | Root Cause | Solution |
|---|---|---|---|
| **1** | **24s High Latency** | Google Gemini fallback rate-limits & latency. | Switched primary LLM provider to **OpenRouter (`meta-llama/llama-3.1-8b-instruct`)**. |
| **2** | **`ValueError: trailing characters`** | Llama 3.1 emitted duplicate JSON tool arguments `{"reason": "no"}{"reason": "no"}`. | Passed `parallel_tool_calls=False` in `openai.LLM(...)`. |
| **3** | **Spoken `<function=hobby>` Markup** | Llama 3.1 generated XML tags in raw text stream. | Added negative prompt directives & `_clean_tts_text()` regex filter. |
| **4** | **Missing SIP Config on Frontend Call** | `execAsync` ran Python without `.env.local`. | Added `from dotenv import load_dotenv; load_dotenv('.env.local')` to API route. |
| **5** | **No Greeting / Silent Call** | `await session.start(...)` blocked the main setup thread indefinitely. | Converted `session.start` to non-blocking task (`asyncio.create_task`). |
| **6** | **Linphone Rang But No Agent** | `create_sip_participant` was called directly without `agent_dispatch`. | Updated `trigger_outbound_practice` to use `agent_dispatch.create_dispatch`. |
| **7** | **`Task destroyed but pending`** | Python garbage collected active background task. | Awaited `session_started` at the end of agent entrypoints. |

---

## 🚀 How to Run

```powershell
# Windows PowerShell
.\start_app.ps1

# Linux / macOS Bash
./start_app.sh
```
