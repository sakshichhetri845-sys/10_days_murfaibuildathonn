# Day 3 — Voice UI & Web Interface

## Overview
Day 3 delivered a modern Next.js web application interface for **BolBuddy**, built using React, TypeScript, Tailwind CSS, and LiveKit Agents UI components.

## Objective
Create a responsive, engaging web UI with real-time audio visualization, session controls, and live conversation transcript streaming.

## What I Built
- Next.js 15 Web Application with TypeScript and Tailwind CSS.
- Animated orb audio visualizer (`bolbuddy-session-view.tsx`) reflecting speaking and listening states.
- Welcome view screen (`welcome-view.tsx`) with instant room connection.
- Live conversation transcript toggle drawer for visual speech review.
- Microphone mute, session control, and persistent memory side panel drawer (`memory-panel.tsx`).

## Implementation
- Frontend entry: `frontend/app/page.tsx`.
- Token route API endpoint: `frontend/app/api/token/route.ts`.
- Components in `frontend/components/app/` and `frontend/components/agents-ui/`.

## User Experience
Learners click "Start Practice", talk directly into their microphone, watch the animated orb react dynamically to their voice, and can toggle live text transcripts.

## Key Features
- Dynamic orb visualizer with active voice states.
- Clean responsive layout for desktop and mobile browsers.
- Real-time token generation for secure LiveKit WebRTC connection.

## Demo Flow
1. Open web page at `http://localhost:3000`.
2. Click **Start Practice Session**.
3. View orb visualization pulsing in response to voice audio.

## Tech Used
- Next.js / React 19 / TypeScript
- Tailwind CSS
- LiveKit Components React (`@livekit/components-react`)
- Lucide Icons & Motion

## Files / Components
- `frontend/app/page.tsx`
- `frontend/components/app/welcome-view.tsx`
- `frontend/components/app/bolbuddy-session-view.tsx`

## Status
**Completed.**
