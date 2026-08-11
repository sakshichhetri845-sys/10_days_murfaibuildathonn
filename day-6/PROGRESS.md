# Day 6 — HealthSaathi Outbound Telephony Agent
**Date:** 2026-08-12

## What Was Built Today

### 🚀 Outbound Telephony Pipeline (New)
- **`backend/src/telephony/outbound/agent.py`** — Full outbound voice agent:
  - Dials SIP participants via LiveKit SIP trunk
  - Multi-LLM fallback: OpenRouter → NVIDIA NIM → Groq → Google Gemini
  - Murf Falcon TTS (voice=Samar, style=Conversation)
  - Deepgram Nova-3 Multilingual STT (en + hi + Hinglish)
  - Silero VAD + LiveKit Multilingual Turn Detector
  - Persistent memory (SQLite) with lookup / save / forget tools
  - Call outcome logging via OutboundCallService
  - Auto-hangup on silence / decline / task completion

- **`backend/src/telephony/outbound/call_service.py`** — SQLite-backed call status tracking
- **`backend/src/telephony/outbound/call_manager.py`** — Scheduled call manager (runs due calls)
- **`backend/src/telephony/outbound/config.py`** — Outbound agent config (SIP trunk, voices)
- **`backend/src/telephony/outbound/dial.py`** — SIP dial helper
- **`backend/src/telephony/outbound/make_call.py`** — Quick call trigger script

### 📡 HTTP API Server (New)
- **`backend/src/api_server.py`** — FastAPI/aiohttp REST server on port 8000:
  - POST /api/outbound/call — trigger an outbound call
  - GET  /api/outbound/history — call history
  - POST /api/outbound/schedule — schedule a future call

### 🎙️ Prompt Architecture (New)
- **`backend/src/prompts/outbound_prompt.py`** — HealthSaathi outbound call script builder
- **`backend/src/prompts/__init__.py`** — Prompt module exports

### 🖥️ Frontend Outbound UI (New)
- **`frontend/app/api/outbound/call/route.ts`** — API route: trigger call
- **`frontend/app/api/outbound/history/route.ts`** — API route: call history
- **`frontend/app/api/outbound/schedule/route.ts`** — API route: schedule call
- **`frontend/components/app/outbound-call-card.tsx`** — Outbound call UI card component

### 🧪 Tests (New)
- **`backend/tests/test_day6_outbound.py`** — LLM-judged eval tests for the outbound agent
- **`backend/tests/test_telephony.py`** — Telephony pipeline integration tests

### 🐛 Bug Fix — VAD / Turn Detector Lag (Today)
- **Problem:** Silero VAD inference was 17-30s slower than realtime; caused TimeoutError in turn detector and 5-7s agent response lag
- **Fix 1:** Switched AgentServer to JobExecutorType.PROCESS — Silero now runs in a subprocess, freeing the asyncio event loop
- **Fix 2:** Raised activation_threshold 0.3 → 0.5 (reduces false VAD triggers on background noise)
- **Fix 3:** Tightened min_endpointing_delay 0.4s → 0.2s; raised max_endpointing_delay 1.2s → 5.0s for more reliable turn detection

## Stack
- LiveKit Agents SDK ~1.4 (PROCESS executor)
- Murf Falcon TTS
- Deepgram Nova-3 (multilingual)
- Google Gemini 2.0 Flash / Groq / NVIDIA NIM / OpenRouter (multi-LLM)
- Silero VAD + LiveKit Multilingual Turn Detector
- Next.js 15 Frontend
- SQLite persistent memory + call log DB

## Notes
- Restart the agent after today's VAD fix — JobExecutorType.PROCESS requires a fresh process start
- SIP trunk ID must be set in .env.local as LIVEKIT_SIP_OUTBOUND_TRUNK_ID
- To trigger a test call: uv run python backend/trigger_outbound_call.py
