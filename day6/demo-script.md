# Day 6 — Outbound Calls Demo Script

This script walks through demonstrating BolBuddy's outbound voice practice calling feature across all core user flows and edge-case scenarios.

---

## Prerequisites
1. Backend agent worker running:
   ```bash
   cd backend
   uv run python src/agent.py dev
   ```
2. Frontend Next.js running:
   ```bash
   cd frontend
   pnpm dev
   ```
3. Credentials set in `backend/.env.local`:
   - `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
   - `LIVEKIT_SIP_TRUNK_ID` (for live phone calls)

---

## Scenario 1 — Successful Scheduled Practice Call

### Steps:
1. Open BolBuddy web interface at `http://localhost:3000`.
2. Scroll to the **Practice Call** section.
3. Enter preferred practice time: `7:30 PM`, Phone: `+919876543210`, Name: `Sakshyam`.
4. Click **"Trigger Test Call Now"** (or send `POST /api/outbound/practice`).

### Expected Dialogue:
- **Phone Rings & User Answers**
- **BolBuddy**: *"Hi Sakshyam, this is BolBuddy. You scheduled an English practice session. Is this still a good time?"*
- **Learner**: *"Yes, this is a great time!"*
- **BolBuddy**: *"Great. Last time we practiced internship interview English. Let's continue with one quick question: Tell me about yourself in three sentences."*
- **Learner**: *"I am a final year computer science student. I enjoy building web applications. I am looking for a software engineering internship."*
- **BolBuddy**: *"That was concise and clear! Excellent job. Keep practicing!"*
- **Call Ends Normally**. Status logged as `COMPLETED`.

---

## Scenario 2 — Learner Declines Practice Call

### Steps:
1. Trigger outbound practice call.
2. Answer the phone.

### Expected Dialogue:
- **BolBuddy**: *"Hi Sakshyam, this is BolBuddy. You scheduled an English practice session. Is this still a good time?"*
- **Learner**: *"No, not right now."*
- **BolBuddy**: *"No problem. I won't continue the session. You can practice whenever you're ready."*
- **Call Ends Disconnected**. Status logged as `DECLINED`. No automatic retry initiated.

---

## Scenario 3 — Learner States They Are Busy

### Steps:
1. Trigger outbound practice call.
2. Answer the phone.

### Expected Dialogue:
- **BolBuddy**: *"Hi Sakshyam, this is BolBuddy. You scheduled an English practice session. Is this still a good time?"*
- **Learner**: *"I'm in a meeting right now."*
- **BolBuddy**: *"That's completely fine. I'll let you get back to your day."*
- **Call Ends Disconnected**. Status logged as `BUSY`.

---

## Scenario 4 — No Answer Handling

### Steps:
1. Trigger outbound practice call to an unanswered line.

### Expected Result:
- Line rings out.
- System logs status: `NO_ANSWER`.
- Zero fake dialogue generated. Conservative retry policy evaluates delay window before any re-attempt.

---

## Scenario 5 — Immediate Hangup Handling

### Steps:
1. Trigger outbound practice call.
2. Answer call and immediately hang up.

### Expected Result:
- System detects user speech committed count is 0.
- System records `IMMEDIATE_HANGUP` in SQLite database.
- Agent worker process continues running cleanly without crashing.

---

## Scenario 6 — Unconfigured / Missing Telephony Credentials

### Steps:
1. Remove `LIVEKIT_SIP_TRUNK_ID` from environment.
2. Click **"Trigger Test Call Now"**.

### Expected Result:
- System returns `PROVIDER_ERROR` status with error: `"Missing configuration environment variables: LIVEKIT_SIP_TRUNK_ID"`.
- Application logs technical error safely with zero secret exposure.
- Agent worker remains healthy and running.
