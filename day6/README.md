# Day 6 — Outbound Calls

## Objective
Enable proactive, automated outbound voice calls for BolBuddy, allowing learners to receive a daily English practice call at their chosen preferred time (#VoiceForBharat challenge).

---

## Use Case
**"Daily practice call at a time the learner picked."**

Language learners often hesitate or procrastinate when initiating spoken practice. By automatically calling the learner at their scheduled time (e.g., 7:00 PM), BolBuddy delivers frictionless, 2–3 minute micro-practice sessions directly to their phone, helping students and job seekers build confidence for job interviews, college vivas, and daily conversations.

---

## Architecture

```
Learner Preference (Next.js UI / API)
  │
  ▼
Outbound Trigger / SQLite Scheduler (backend/src/scheduler.py & outbound.py)
  │
  ▼
LiveKit SIP Dispatch (backend/src/telephony.py -> CreateSIPParticipant)
  │
  ▼
SIP Outbound Trunk (PSTN / Twilio / Linphone)
  │
  ▼
Learner Phone Rings (PSTN / Linphone)
  │ (Learner Answers)
  ▼
BolBuddy Voice Agent Worker (backend/src/agent.py)
  │
  ├── Deepgram Nova-3 Multilingual STT (en + hi + hinglish)
  ├── NVIDIA LLM (meta/llama-3.1-70b-instruct / z-ai/glm-5.2)
  └── Murf Falcon TTS (Streaming Audio, voice="Anisha")
```

- **Pipeline Components**: Deepgram Nova-3 Multilingual STT, NVIDIA LLM, Murf Falcon TTS, LiveKit Agents SDK (`~1.4`), SQLite persistent storage.

---

## What Was Built
1. **Learner Preference Storage**: Stored practice preferences (`preferred_practice_time`, `timezone`, `phone_number`, `practice_topic`) in SQLite database (`bolbuddy_memory.db`).
2. **LiveKit SIP Outbound Integration**: Clean telephony dispatch layer supporting `LIVEKIT_SIP_OUTBOUND_TRUNK_ID` via LiveKit Telephony API (`CreateSIPParticipantRequest`).
3. **Outbound Call Opening**: Enforced strict 3-part opening:
   - Who is calling: *"BolBuddy, your English practice companion"*
   - Why they are calling: *"You scheduled your daily practice call for this time"*
   - How to stop: *"If you'd rather not practice now, just say so and I'll end the call."*
4. **Deterministic Call State Machine**: Tracked 7 call states (`SCHEDULED` → `CALLING` → `CONNECTED` → `GREETING` → `PRACTICE` → `FEEDBACK` → `COMPLETED` / `NO_ANSWER` / `BUSY` / `DECLINED` / `STOPPED`).
5. **Conservative Retry & Opt-Out Policy**: Immediate opt-out cancellation on user request; transient failure retry delay window (`OUTBOUND_RETRY_DELAY_SECONDS=300`, `OUTBOUND_MAX_RETRIES=1`).
6. **Frontend Setting Section**: Added a compact "Daily Practice Call" section in Next.js frontend UI (`practice-call-section.tsx`) to configure preferred practice time, phone number, and test calls.

---

## Configuration

Required environment variables in `backend/.env.local`:

```bash
# LiveKit Core
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# LiveKit SIP Outbound Telephony
LIVEKIT_SIP_OUTBOUND_TRUNK_ID=ST_your_sip_trunk_id

# Optional SIP Provider Credentials (e.g. Twilio or Linphone)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+12025550123

# LLM & Voice Pipeline
NVIDIA_API_KEY=your_nvidia_api_key
MURF_API_KEY=your_murf_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key

# Outbound Controls
OUTBOUND_CALL_ENABLED=true
OUTBOUND_MAX_RETRIES=1
OUTBOUND_RETRY_DELAY_SECONDS=300
```

---

## Running

### 1. Start the Voice Agent Worker & Scheduler
```bash
cd backend
uv run python src/agent.py dev
```

### 2. Schedule a Daily Practice Call via CLI
```bash
cd backend
uv run python -c "import sys; sys.path.append('src'); from schedule_model import create_or_update_schedule; create_or_update_schedule(user_id='sakshyam', phone_number='+9779876543210', preferred_time='19:00', timezone='Asia/Kathmandu')"
```

### 3. Manually Trigger an Outbound Test Call
```bash
cd backend
uv run python -m outbound test-call +9779876543210 sakshyam
```

### 4. Run Frontend UI
```bash
cd frontend
pnpm dev
```
Open `http://localhost:3000` to configure daily practice time and test calls.

---

## Test Scenario

1. **Trigger Call**: Execute manual test trigger CLI or UI button.
2. **Phone Rings**: Phone / Linphone client receives incoming call.
3. **Learner Answers**: Connection established.
4. **BolBuddy Opening**: BolBuddy speaks short 3-part opening:
   > *"Hi Sakshyam, this is BolBuddy, your English practice companion. You scheduled your daily practice call for this time. If you'd rather not practice now, just say so and I'll end the call."*
5. **Learner Responds**:
   - If learner says *"Sure, let me practice"*: BolBuddy asks a practice question (e.g. *"Tell me about your day in two sentences."*).
   - If learner speaks Hinglish (*"Ha, thoda busy hoon but let's try"*): BolBuddy responds in natural Hinglish.
   - If learner says *"Not right now"*: BolBuddy says *"No problem. I'll let you get back to your day. Bye!"* and disconnects.
6. **Call Recorded**: Final status (`COMPLETED`, `DECLINED`, `BUSY`, etc.) logged in SQLite database.

---

## Failure Handling

- **Missing Configuration**: If `LIVEKIT_SIP_OUTBOUND_TRUNK_ID` is missing, `TelephonyConfigurationError` is raised with a user-friendly error message. Never fabricates fake calls.
- **No Answer / Busy**: Automatically tracked as `NO_ANSWER` or `BUSY` without crashing the agent process.
- **User Opt-Out**: Saying *"stop calling me"* or *"cancel my calls"* immediately cancels future schedules and sets opt-out status.
- **Error Shielding**: No raw tracebacks or internal database IDs are spoken to the user.

---

## Voice Behaviour

- **Short Responses**: Agent replies are strictly limited to 1–2 short sentences (under 15–20 words).
- **Natural Language Support**: Supports English, Hindi, and code-mixed Hinglish.
- **No Filler**: Zero preamble, zero repetition of user answers, zero XML/JSON tool leakage.

---

## Existing Pipeline

The core voice pipeline is **100% preserved**:
- **STT**: Deepgram Nova-3 Multilingual (`language="multi"`)
- **LLM**: Primary NVIDIA API (`meta/llama-3.1-70b-instruct`) with Google Gemini fallback
- **TTS**: Murf Falcon Streaming (`voice="Anisha", style="Conversation"`)
- **VAD**: Silero VAD

---

## Limitations

- **Live PSTN Telephony**: Initiating real outbound PSTN calls requires an active LiveKit SIP Outbound Trunk (`LIVEKIT_SIP_OUTBOUND_TRUNK_ID`) connected to Twilio or Linphone SIP server.
- **Challenge Demo**: Provides both background polling scheduler (`scheduler.py`) and manual CLI trigger (`python -m outbound test-call`) for recording demo videos.

---

## Day 6 Completion Checklist

- [x] Outbound telephony connected
- [x] Learner practice time stored
- [x] Outbound call triggered
- [x] Phone/Linphone rings
- [x] BolBuddy opens the call correctly
- [x] Short English practice completed
- [x] Existing voice pipeline preserved
- [x] Failure path tested
- [x] Demo recorded
- [x] LinkedIn post published
