# Day 6 — HealthSaathi Outbound Telephony Agent
**Date:** 2026-08-12

## What Was Built Today

### 🚀 Outbound Telephony Pipeline
- Full outbound SIP voice agent (`backend/src/telephony/outbound/agent.py`)
  - Multi-LLM fallback chain: OpenRouter -> NVIDIA NIM -> Groq -> Google Gemini
  - Murf Falcon TTS (voice=Samar, style=Conversation)
  - Deepgram Nova-3 Multilingual STT (en + hi + Hinglish)
  - Silero VAD + LiveKit MultilingualModel turn detector
  - Persistent SQLite memory with lookup / save / forget tools
  - Call outcome logging via OutboundCallService
  - Auto-hangup on silence / decline / task completion

### 📡 HTTP API Server
- REST API on port 8000 (`backend/src/api_server.py`)
  - POST /api/outbound/call — trigger an outbound call
  - GET  /api/outbound/history — call history
  - POST /api/outbound/schedule — schedule a future call

### 🎙️ Prompt Architecture
- `backend/src/prompts/outbound_prompt.py` — HealthSaathi outbound call script builder

### 🖥️ Frontend Outbound UI
- `frontend/app/api/outbound/` — Next.js API routes (call / history / schedule)
- `frontend/components/app/outbound-call-card.tsx` — Outbound call trigger UI card

### 🧪 Tests
- `backend/tests/test_day6_outbound.py` — LLM-judged eval tests for outbound agent
- `backend/tests/test_telephony.py` — Telephony pipeline integration tests

### 🐛 Bug Fix — VAD / Turn Detector Lag
- Problem: Silero VAD inference was 17-30s slower than realtime; caused TimeoutError in turn detector and 5-7s response lag
- Fix 1: Switched to JobExecutorType.PROCESS so Silero runs in a subprocess (frees asyncio event loop)
- Fix 2: Raised VAD activation_threshold 0.3 -> 0.5 to reduce false triggers
- Fix 3: Tightened endpointing delays (min 0.4->0.2s, max 1.2->5.0s)

## Notes
- Restart the backend agent after the VAD fix for PROCESS executor to take effect
- Set LIVEKIT_SIP_OUTBOUND_TRUNK_ID in .env.local before making outbound calls
- Trigger a test call: uv run python backend/trigger_outbound_call.py
