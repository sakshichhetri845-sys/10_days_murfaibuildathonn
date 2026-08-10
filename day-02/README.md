# Day 2 — Personality & Safety Guardrails

## Overview
Day 2 shaped **BolBuddy** into a warm, encouraging English-speaking companion specifically tuned for Indian learners preparing for job interviews, vivas, presentations, and daily conversation.

## Objective
Establish a distinctive system prompt, conversation principles, safety guardrails, and concise response guidelines.

## What I Built
- Modular System Prompt architecture ([backend/src/prompts/](file:///c:/Users/livel/Downloads/murffff/murf-livekit-starter/backend/src/prompts/)).
- Identity definition (`identity.py`): Warm Indian English practice companion.
- Conversation principles (`conversation_principles.py`): Short 1-2 sentence replies (< 20 words), no robotic fluff, natural code-mixing support (English + Hindi + Hinglish).
- Guardrails (`guardrails.py`): Prevents non-educational roleplay, blocks technical jargon leakage, refuses harmful queries politely.

## Implementation
- `backend/src/prompts/system_prompt.py` compiles modular guidelines into a compact system prompt (~340 tokens).
- Dynamic tone adaptation for interview prep, viva practice, and daily speech.

## User Experience
Learners experience an empathetic, highly conversational AI partner that speaks in short, natural sentences without robotic lectures or overwhelming feedback.

## Key Features
- Ultra-concise response style (1-2 sentences maximum).
- Indian context & Hinglish register support.
- Safety guardrails preventing invalid tool leakage or out-of-scope behavior.

## Demo Flow
1. User: *"Hi BolBuddy, I feel nervous speaking English in interviews."*
2. BolBuddy: *"That's totally normal! We can practice together step by step. What would you like to start with?"*

## Tech Used
- Python 3.10+
- LiveKit Agents Prompt Engine
- Modular Prompt Architecture

## Files / Components
- `backend/src/prompts/system_prompt.py`
- `backend/src/prompts/identity.py`
- `backend/src/prompts/guardrails.py`

## Status
**Completed.**
