# 10 Days Murf AI Buildathon — Day 6 🚀

Welcome to **Day 6** of the **10 Days Murf AI Buildathon** by **Sakshi Chhetri** ([@sakshichhetri845-sys](https://github.com/sakshichhetri845-sys)).

Day 6 introduces the **HealthSaathi Outbound Telephony Agent** — an automated AI agent that calls patients for health follow-ups using a full real-time voice pipeline.

---

## 📁 Day 6 Structure

`
day-6/
├── backend/    # Python outbound voice agent (LiveKit Agents + Murf Falcon TTS)
├── frontend/   # Next.js UI with outbound call trigger card
├── PROGRESS.md # Day 6 progress log
└── README.md   # This file
`

---

## 🆕 What's New in Day 6

| Feature | Details |
|---------|---------|
| **Outbound SIP Telephony** | Agent dials patients via LiveKit SIP trunk |
| **Multi-LLM Fallback** | OpenRouter → NVIDIA NIM → Groq → Google Gemini |
| **HTTP API Server** | REST endpoints to trigger / schedule / review calls |
| **Frontend Outbound Card** | UI to trigger and monitor outbound calls |
| **VAD Bug Fix** | Silero VAD moved to PROCESS executor — eliminates 17-30s lag |

---

## 🛠 How to Run

### Backend (Outbound Agent)
`ash
cd day-6/backend
uv sync
uv run python src/agent.py download-files   # first time only
uv run python src/telephony/outbound/agent.py dev
`

### Frontend
`ash
cd day-6/frontend
pnpm install
pnpm dev
`

### Trigger a Test Call
`ash
cd day-6/backend
uv run python trigger_outbound_call.py
`

---

## 🔑 Environment Variables

Copy .env.example to .env.local in both ackend/ and rontend/ and fill in:

| Variable | Description |
|----------|------------|
| LIVEKIT_URL | LiveKit Cloud WebSocket URL |
| LIVEKIT_API_KEY | LiveKit API key |
| LIVEKIT_API_SECRET | LiveKit API secret |
| MURF_API_KEY | Murf AI API key |
| DEEPGRAM_API_KEY | Deepgram Nova-3 API key |
| GOOGLE_API_KEY | Google Gemini API key |
| LIVEKIT_SIP_OUTBOUND_TRUNK_ID | LiveKit SIP trunk for outbound calls |
| GROQ_API_KEY | (Optional) Groq LLM API key |
| OPENROUTER_API_KEY | (Optional) OpenRouter API key |

---

## 🔗 Links

- [Murf Falcon TTS Docs](https://murf.ai/api/docs/text-to-speech/streaming)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- [LiveKit Agents Docs](https://docs.livekit.io/agents)
- [Deepgram Nova-3 Docs](https://developers.deepgram.com)

## License

MIT — see [LICENSE](../LICENSE).
