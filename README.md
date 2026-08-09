# 10 Days Murf AI Buildathon 🚀

Welcome to the **10 Days Murf AI Buildathon** repository by **Sakshi Chhetri** ([@sakshichhetri845-sys](https://github.com/sakshichhetri845-sys)).

This repository tracks daily progress, implementations, and voice AI projects built during the 10-day buildathon, powered by **Murf Falcon TTS**, **LiveKit Agents**, **Deepgram**, and **Google Gemini / Groq**.

---

## 📁 Repository Structure

```
10_days_murfaibuildathonn/
├── day-1/       # Day 1: Murf LiveKit Starter Voice Agent
├── day-2/       # Day 2: HealthSaathi — Voice-First AI Health Companion
└── README.md    # Repository overview
```

---

## 📅 Daily Projects & Progress

### 🔹 [Day 1: Murf LiveKit Starter Voice Agent](./day-1)
* **Goal**: Build and configure the foundation of the voice agent pipeline with Speech-to-Text, LLM processing, and Murf Falcon Text-to-Speech.
* **Key Features**:
  * LiveKit Agent SDK integration.
  * Murf Falcon TTS streaming integration.
  * Deepgram Nova-3 Speech-to-Text.
  * Basic interactive frontend session view.

### 🔹 [Day 2: HealthSaathi — Voice-First AI Health Companion](./day-2)
* **Goal**: Transform the voice agent into **HealthSaathi**, an accessible, empathetic AI health companion for healthcare access in Bharat.
* **Key Features**:
  * **Murf Falcon TTS (`Samar`)**: Configured with `Samar` (Indian English male voice) for natural healthcare conversations.
  * **Modular System Prompt Architecture**: Split into 8 focused prompt modules in `backend/src/prompts/` (`identity`, `language`, `objectives`, `style`, `guardrails`, `knowledge`, `greeting`, `conversation_principles`).
  * **HealthSaathi UI**: Full responsive Next.js frontend with doctor visit preparation features, health terms simplification, and accessible design.

### 🔹 [Day 4: Progress Update](./day-4)
* **Goal**: Keep track of the next buildathon day in the same split backend/frontend project structure.
* **Key Features**:
  * Day 4 workspace folders for backend and frontend progress tracking.
  * Notes for backend restart and LiveKit startup verification.
  * Space to continue implementation work without disrupting earlier days.

---

## 🛠 How to Run Any Day's Project

Navigate into the specific day folder (e.g. `cd day-2`) and follow the setup commands:

### Backend
```bash
cd day-2/backend
uv sync
uv run python src/agent.py dev
```

### Frontend
```bash
cd day-2/frontend
pnpm install
pnpm dev
```
