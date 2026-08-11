# Backend — HealthSaathi Outbound Telephony Agent (Day 6)

The Python backend for the **HealthSaathi Outbound Telephony Agent**. It runs a real-time outbound voice AI pipeline using [LiveKit Agents](https://docs.livekit.io/agents), dialing patients automatically for health follow-up calls.

## How It Works

`
Agent dials patient (SIP) → Patient answers
→ [Deepgram STT] → text → [LLM] → response → [Murf Falcon TTS] → audio → Patient hears
`

LiveKit handles real-time audio transport. The agent connects as a SIP participant, speaks the greeting, listens for patient responses, and manages the full conversation flow.

## Pipeline Components

| Component | Technology |
|-----------|-----------|
| **STT** | Deepgram Nova-3 Multilingual (en + hi + Hinglish) |
| **LLM** | OpenRouter / NVIDIA NIM / Groq / Google Gemini (auto-fallback) |
| **TTS** | Murf Falcon (voice=Samar, style=Conversation) |
| **VAD** | Silero (PROCESS executor — no event loop blocking) |
| **Turn Detection** | LiveKit MultilingualModel |
| **Memory** | SQLite persistent memory (lookup / save / forget) |
| **Transport** | LiveKit SIP Trunk |

## Setup

### 1. Install dependencies

`ash
cd backend
uv sync
`

### 2. Configure environment

`ash
cp .env.example .env.local
`

Fill in your keys in .env.local:

| Variable | Where to get it |
|----------|----------------|
| LIVEKIT_URL | [LiveKit Cloud](https://cloud.livekit.io/) → Settings |
| LIVEKIT_API_KEY | [LiveKit Cloud](https://cloud.livekit.io/) → Settings |
| LIVEKIT_API_SECRET | [LiveKit Cloud](https://cloud.livekit.io/) → Settings |
| MURF_API_KEY | [murf.ai/api/dashboard](https://murf.ai/api/dashboard) |
| DEEPGRAM_API_KEY | [deepgram.com](https://console.deepgram.com/) |
| GOOGLE_API_KEY | [aistudio.google.com](https://aistudio.google.com/apikey) |
| LIVEKIT_SIP_OUTBOUND_TRUNK_ID | LiveKit Cloud → SIP → Outbound Trunks |
| GROQ_API_KEY | [console.groq.com](https://console.groq.com/) (optional) |
| OPENROUTER_API_KEY | [openrouter.ai](https://openrouter.ai/) (optional) |

### 3. Download models

`ash
uv run python src/agent.py download-files
`

This downloads the Silero VAD and LiveKit turn detector models.

### 4. Run the outbound agent

`ash
# Development mode
uv run python src/telephony/outbound/agent.py dev

# Trigger a test call manually
uv run python trigger_outbound_call.py
`

## Project Structure

`
backend/
├── src/
│   ├── telephony/
│   │   └── outbound/
│   │       ├── agent.py          # Outbound voice agent entrypoint
│   │       ├── call_service.py   # SQLite call status tracking
│   │       ├── call_manager.py   # Scheduled call manager
│   │       ├── config.py         # Agent configuration
│   │       └── dial.py           # SIP dial helper
│   ├── prompts/
│   │   └── outbound_prompt.py    # HealthSaathi outbound call script builder
│   ├── api_server.py             # REST API server (port 8000)
│   ├── memory_service.py         # Persistent memory service
│   ├── memory_tools.py           # Agent memory tools
│   └── database.py               # SQLite DB initialization
├── tests/
│   ├── test_day6_outbound.py     # LLM-judged eval tests for outbound agent
│   └── test_telephony.py         # Telephony pipeline integration tests
├── trigger_outbound_call.py      # Quick CLI call trigger
├── .env.example                  # Environment variable template
└── pyproject.toml                # Python dependencies (uv)
`

## HTTP API Server

The agent starts a REST API on port 8000:

`ash
# Trigger an outbound call
POST http://localhost:8000/api/outbound/call
{
  "phone_number": "+91XXXXXXXXXX",
  "user_id": "riya_verma",
  "name": "Riya"
}

# Get call history
GET http://localhost:8000/api/outbound/history

# Schedule a future call
POST http://localhost:8000/api/outbound/schedule
{
  "phone_number": "+91XXXXXXXXXX",
  "scheduled_at": "2026-08-12T10:00:00"
}
`

## VAD Configuration (Day 6 Fix)

The key performance fix in Day 6 — Silero VAD now runs in a **subprocess** (JobExecutorType.PROCESS) to prevent blocking the asyncio event loop:

`python
# agent.py
server = AgentServer(job_executor_type=JobExecutorType.PROCESS)

silero.VAD.load(
    activation_threshold=0.5,   # raised from 0.3 — fewer false triggers
    min_silence_duration=0.2,   # lowered from 0.3s — faster turn end
)

AgentSession(
    min_endpointing_delay=0.2,  # respond sooner after silence
    max_endpointing_delay=5.0,  # allow turn detector more time
)
`

## Testing

`ash
uv run pytest
`

## Voice Options

| Voice ID | Description |
|----------|------------|
| Samar | Indian English, male (default) |
| Anisha | Indian English, female |
| Pooja | Indian English, female |
| Amara | US English, female |

Browse all 150+ voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)

## Links

- [Murf Falcon TTS Docs](https://murf.ai/api/docs/text-to-speech/streaming)
- [LiveKit Agents Docs](https://docs.livekit.io/agents)
- [Deepgram Nova-3 Docs](https://developers.deepgram.com)

## License

MIT — see [LICENSE](../../LICENSE).
