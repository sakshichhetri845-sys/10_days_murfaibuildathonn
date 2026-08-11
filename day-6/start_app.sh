#!/bin/bash

# Start all 3 HealthSaathi services (Inbound Agent, Outbound Agent Worker + API Server, Frontend App)
echo "========================================================"
echo " HealthSaathi - Day 6 Outbound Voice Telephony System"
echo " 10 Days of Voice Agents (#VoiceForBharat Challenge)"
echo "========================================================"

echo "Launching 3 services:"
echo " 1. [Terminal 1] Inbound Web Agent (src/agent.py)"
echo " 2. [Terminal 2] Outbound Telephony Worker & API Server (src/telephony/outbound/agent.py + src/api_server.py)"
echo " 3. [Terminal 3] Frontend Web App (http://localhost:3000)"

(cd backend && uv run python src/agent.py dev) &
(cd backend && uv run python src/api_server.py) &
(cd backend && uv run python src/telephony/outbound/agent.py dev) &
(cd frontend && pnpm dev) &

# Wait for background jobs
wait
