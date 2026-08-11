# Frontend — HealthSaathi Voice Agent UI (Day 6)

The React/Next.js frontend for the **HealthSaathi Voice Agent** with Day 6's new **Outbound Call** feature. Built with [LiveKit Agents UI](https://livekit.io/ui) components, it provides a polished interface for both live voice sessions and triggering outbound patient calls.

## Features

- Real-time voice interaction with the HealthSaathi agent
- **NEW (Day 6):** Outbound call trigger card — dial patients for health follow-ups
- Multiple audio visualizer styles (ar, grid, adial, wave, ura)
- Light/dark theme switching with system preference detection
- Customizable branding via pp-config.ts
- Chat transcript display during voice sessions
- Camera video and screen sharing support

## Setup

### 1. Install dependencies

`ash
cd frontend
pnpm install
`

### 2. Configure environment

`ash
cp .env.example .env.local
`

Fill in your LiveKit credentials:

`env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
AGENT_NAME=my-agent
`

### 3. Run

`ash
pnpm dev
`

Open [http://localhost:3000](http://localhost:3000). Make sure the backend agent is running too.

## Outbound Call UI (Day 6)

A new **Outbound Call Card** (components/app/outbound-call-card.tsx) lets you trigger patient health follow-up calls directly from the UI.

The frontend calls these new API routes (backed by the Python API server on port 8000):

| Route | Method | Description |
|-------|--------|-------------|
| /api/outbound/call | POST | Trigger an outbound call |
| /api/outbound/history | GET | View call history |
| /api/outbound/schedule | POST | Schedule a future call |

## Customization

### Branding (pp-config.ts)

`	s
export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'HealthSaathi',
  pageTitle: 'HealthSaathi — AI Health Companion',
  pageDescription: 'Your voice-first AI health companion powered by Murf Falcon TTS',
  accent: '#6366F1',
  startButtonText: 'Start health check-in',
};
`

### Audio Visualizers

Set udioVisualizerType in pp-config.ts:

| Type | Description |
|------|------------|
| ar (default) | Vertical bars |
| grid | Dot grid |
| adial | Circular bars |
| wave | Oscilloscope wave |
| ura | Shader-based glow |

## Project Structure

`
frontend/
├── app/
│   ├── page.tsx                          # Main page
│   ├── layout.tsx                        # Root layout
│   └── api/
│       ├── token/route.ts                # LiveKit token endpoint
│       └── outbound/
│           ├── call/route.ts             # Trigger outbound call
│           ├── history/route.ts          # Call history
│           └── schedule/route.ts         # Schedule call
├── components/
│   ├── agents-ui/                        # Agents UI (visualizers, controls, chat)
│   ├── app/
│   │   ├── outbound-call-card.tsx        # NEW: Outbound call trigger card
│   │   ├── healthsaathi-session-view.tsx # Main session view
│   │   ├── welcome-view.tsx              # Welcome / connect screen
│   │   └── view-controller.tsx           # View state management
│   ├── ai-elements/                      # AI conversation elements
│   └── ui/                               # Shadcn/ui primitives
├── hooks/                                # React hooks
├── styles/                               # Global CSS
├── app-config.ts                         # Branding and feature configuration
└── package.json                          # Dependencies (pnpm)
`

## Deployment

### Vercel

Set these environment variables:

- LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
- AGENT_NAME (optional — for explicit agent dispatch)

The frontend and backend connect independently to LiveKit. Use the same LiveKit project credentials on both.

## Links

- [LiveKit Agents UI](https://livekit.io/ui)
- [LiveKit JavaScript SDK](https://github.com/livekit/client-sdk-js)
- [Murf Falcon TTS](https://murf.ai/api/docs/text-to-speech/streaming)

## License

MIT — see [LICENSE](../../LICENSE).
