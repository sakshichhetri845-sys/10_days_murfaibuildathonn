# Day 1 — Basic Voice Agent Pipeline

## Overview
Day 1 focused on initializing the core real-time voice pipeline for **BolBuddy**, establishing duplex speech communication between the user and the assistant with sub-second voice latency.

## Objective
Build a real-time streaming voice agent using LiveKit Agents, Deepgram Speech-to-Text (STT), and Murf Falcon Text-to-Speech (TTS).

## What I Built
- LiveKit WebRTC session management with automatic turn detection using Silero VAD.
- Deepgram Nova-3 multilingual STT integration (`model="nova-3", language="multi"`).
- Murf Falcon streaming TTS output (`voice="Anisha", style="Conversation"`).
- Prewarming of VAD models to minimize first-turn latency.

## Implementation
- Pipeline setup in [backend/src/agent.py](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/agent.py).
- Process prewarming for Silero VAD.
- Audio streaming configuration with `min_sentence_len=1` for immediate TTS generation.

## User Experience
The user opens the application, connects via LiveKit, speaks in English or Hinglish, and receives instant low-latency voice responses.

## Key Features
- Low-latency real-time voice streaming.
- Multilingual speech recognition.
- Automatic voice activity detection (VAD).

## Demo Flow
1. Connect to voice room.
2. Say *"Hello BolBuddy!"*
3. Hear immediate spoken greeting from BolBuddy.

## Tech Used
- LiveKit Agents SDK (`livekit-agents`)
- Deepgram Nova-3 STT
- Murf Falcon TTS
- Silero VAD

## Files / Components
- `backend/src/agent.py`
- `start_app.ps1` / `start_app.sh`

## Status
**Completed.**
