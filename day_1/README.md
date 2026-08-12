# Day 1 — Basic Voice Agent Pipeline (Health Access Track)

## Progress & Milestones Achieved
- [x] Initialized LiveKit WebRTC session management for real-time duplex audio transport.
- [x] Integrated Deepgram Nova-3 Speech-to-Text (`model="nova-3", language="multi"`) supporting English, Hindi, and Hinglish.
- [x] Integrated Murf Falcon streaming Text-to-Speech (`voice="Anisha", style="Conversation"`).
- [x] Prewarmed Silero VAD (Voice Activity Detection) to eliminate first-turn latency.
- [x] Achieved sub-second end-to-end voice latency for interactive health access conversations.

---

## Overview
Day 1 established the core real-time voice infrastructure for **HealthSathi**, a voice-first health access assistant. The pipeline enables bidirectional, low-latency audio streaming directly between the user's browser microphone and the agent backend.

---

## Objective
Build a real-time streaming voice agent using LiveKit Agents, Deepgram Speech-to-Text (STT), and Murf Falcon Text-to-Speech (TTS) configured for the Health Access track.

---

## Architecture & Implementation

```
User Microphone
      ↓ (WebRTC Audio Stream)
LiveKit Agent Server
      ↓
Deepgram Nova-3 STT (Multilingual Transcription)
      ↓
LLM Pipeline (HealthSathi Context Processing)
      ↓
Murf Falcon TTS (Streaming Audio Generation, voice="Anisha")
      ↓ (WebRTC Audio Stream)
User Speaker
```

- **Pipeline Entrypoint**: [backend/src/agent.py](file:///c:/Users/livel/Downloads/murffff/sakshi/backend/src/agent.py)
- **Voice Activity Detection**: Silero VAD tuned with 0.1s minimum speech duration and 0.2s silence threshold.
- **Audio Streaming Pacing**: Murf Falcon TTS initialized with `min_sentence_len=1` for instant audio playback.

---

## User Experience
1. User connects to the LiveKit session room via the HealthSathi web interface.
2. User speaks naturally in English, Hindi, or Hinglish describing health questions or symptoms.
3. HealthSathi greets the user warmly as a health access companion and responds with helpful, non-diagnostic spoken guidance.

---

## Tech Stack
- **Voice Transport**: LiveKit Agents SDK (`livekit-agents ~1.4`)
- **Speech-to-Text**: Deepgram Nova-3 (`language="multi"`)
- **Text-to-Speech**: Murf Falcon TTS (`voice="Anisha"`)
- **VAD**: Silero VAD
- **Language**: Python 3.10+

---

## Status
**Day 1 Completed — HealthSathi Foundation Active.**
