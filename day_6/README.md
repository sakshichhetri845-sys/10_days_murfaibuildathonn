# Day 6 — Outbound Telephony & Scheduled Health Follow-up Calls

This directory documents the Day 6 outbound telephony capabilities for **HealthSathi**, featuring **Scheduled Health Follow-up Calls**, **Linphone SIP integration**, **LiveKit SIP Trunking**, **Murf Falcon TTS (Anisha voice)**, and **Deepgram Nova-3 Multilingual STT**.

---

## 🌟 Key Capabilities Completed in Day 6

1. **Scheduled Health Follow-up / Reminder Calls**:
   - Outbound use case: Scheduled health follow-up and medication reminder calls explicitly requested by users via frontend or voice conversation.
   - Clear 3-part opening:
     1. Identifies who is calling (*"Hi, this is HealthSathi..."*).
     2. Explains why (*"I'm calling for your scheduled health follow-up..."*).
     3. Explains how to end/stop (*"Is now a good time? If not, just say no or stop to end the call."*).

2. **Multilingual Speech Recognition (`nova-3` `multi`)**:
   - Deepgram Nova-3 with `language="multi"` and `smart_format=True` for seamless transcription of English, Hindi, and Hinglish.

3. **Murf Falcon Ultra-Fast Audio Synthesis**:
   - Voice: `Anisha` (`style="Conversation"`). Includes sanitization via `_clean_tts_text()` to prevent XML tags or JSON markup from reaching speech audio.

4. **Zero Obsolete Dependencies**:
   - Outbound agent (`HealthSathiOutboundAgent`) is completely decoupled from BolBuddy English scoring modules.

5. **Frontend Reminders Drawer & Call Trigger**:
   - [health-reminders-section.tsx](file:///c:/Users/livel/Downloads/murffff/sakshi/frontend/components/app/health-reminders-section.tsx): Users can enter their phone number or Linphone ID and select preset health reminder types.

6. **LiveKit Agent Dispatch Architecture**:
   - Uses LiveKit `CreateAgentDispatchRequest` (`agent_name="outbound-agent"`), ensuring LiveKit Cloud connects the dedicated telephony worker to dial the phone/SIP app and speak immediately upon answer.

---

## 🚀 How to Run

```powershell
# Windows PowerShell
.\start_app.ps1

# Linux / macOS Bash
./start_app.sh
```
