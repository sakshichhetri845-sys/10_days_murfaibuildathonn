#!/bin/bash

# Load backend environment variables if present
if [ -f "backend/.env.local" ]; source backend/.env.local; fi

if [[ "$LIVEKIT_URL" != wss://* ]] && command -v livekit-server >/dev/null 2>&1; then
  livekit-server --dev &
else
  echo "Using configured LIVEKIT_URL: ${LIVEKIT_URL:-wss://...}"
fi

(cd backend && uv run python src/agent.py dev ${LIVEKIT_URL:+--url "$LIVEKIT_URL"} ${LIVEKIT_API_KEY:+--api-key "$LIVEKIT_API_KEY"} ${LIVEKIT_API_SECRET:+--api-secret "$LIVEKIT_API_SECRET"}) &
(cd frontend && pnpm dev) &

# Wait for all background jobs
wait
