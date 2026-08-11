"""
HealthSaathi Outbound Telephony Agent — Day 6 Voice Agent.

Initiates automated health follow-up calls at the user's requested time.
Integrates HealthSaathi's complete voice pipeline:
- Deepgram Nova-3 Multilingual STT (en + hi + hinglish)
- Primary NVIDIA / OpenRouter / Groq LLM (with Google Gemini fallback)
- Murf Falcon TTS (voice="Samar" / "en-US-terrell")
- Silero VAD + LiveKit Agents SDK (~1.4)
- Persistent Memory (db.py & memory_tools.py)
- Call outcome logging (OutboundCallService)
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
from typing import Optional

import httpx
from dotenv import load_dotenv
from livekit import api, rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.agents.job import JobExecutorType
from livekit.plugins import deepgram, google, murf, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Add backend root directory and src directory to sys.path for robust imports
_backend_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_src_root = os.path.join(_backend_root, "src")
for _p in [_backend_root, _src_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.database import init_db
    from src.memory_service import MemoryService
    from src.memory_tools import (
        forget_my_data as fn_forget_my_data,
    )
    from src.memory_tools import (
        lookup_user_memory as fn_lookup_user_memory,
    )
    from src.memory_tools import (
        save_user_memory as fn_save_user_memory,
    )
    from src.memory_tools import (
        what_do_you_remember as fn_what_do_you_remember,
    )
    from src.prompts.outbound_prompt import build_outbound_instructions
    from src.telephony.outbound.call_service import OutboundCallService
except ImportError:
    from database import init_db
    from memory_service import MemoryService
    from memory_tools import (
        forget_my_data as fn_forget_my_data,
    )
    from memory_tools import (
        lookup_user_memory as fn_lookup_user_memory,
    )
    from memory_tools import (
        save_user_memory as fn_save_user_memory,
    )
    from memory_tools import (
        what_do_you_remember as fn_what_do_you_remember,
    )
    from prompts.outbound_prompt import build_outbound_instructions
    from telephony.outbound.call_service import OutboundCallService


logger = logging.getLogger("telephony.outbound.agent")
load_dotenv(".env.local")

CALLEE_IDENTITY = "phone-user"


def _prune_history(session: AgentSession, max_turns: int = 6) -> None:
    """Keep chat context history trimmed to prevent context window token bloat and reduce LLM latency."""
    try:
        hist = getattr(session, "history", None) or getattr(session, "chat_ctx", None)
        if hist and hasattr(hist, "truncate"):
            hist.truncate(max_items=max_turns)
            logger.info("Pruned chat context history to prevent token bloat.")
        elif hist and hasattr(hist, "messages"):
            msgs = hist.messages
            if len(msgs) > max_turns + 1:
                system_msg = (
                    [msgs[0]]
                    if (
                        msgs
                        and getattr(msgs[0], "role", None) in ("system", "developer")
                    )
                    else []
                )
                recent_msgs = msgs[-max_turns:]
                hist.messages = system_msg + [
                    m for m in recent_msgs if m not in system_msg
                ]
                logger.info(f"Pruned chat history to {len(hist.messages)} messages.")
    except Exception as e:
        logger.warning(f"Failed to prune chat history: {e}")


def _clean_tts_text(text: str) -> str:
    """Sanitize spoken text output to ensure no raw tool tags, XML, or JSON reach Murf Falcon TTS."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\{[\s\S]*?\}", "", text)
    text = re.sub(r"function\s*[:=]?\s*\w+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[`*_~#]", "", text)
    return re.sub(r"\s+", " ", text).strip()


class HealthSaathiOutboundAgent(Agent):
    def __init__(
        self,
        ctx: JobContext,
        instructions: str,
        initial_greeting: Optional[str] = None,
    ) -> None:
        super().__init__(instructions=instructions)
        self.ctx = ctx
        self._initial_greeting = (
            initial_greeting
            or "Namaste, this is HealthSaathi. I'm calling for a quick health follow-up. Am I speaking with Riya?"
        )

    async def on_enter(self) -> None:
        """Speak the outbound greeting as soon as the agent joins."""
        if self._initial_greeting:
            await self.session.say(
                _clean_tts_text(self._initial_greeting), allow_interruptions=True
            )

    @function_tool
    async def lookup_user_memory(
        self,
        context: RunContext,
        user_id: Optional[str] = None,
    ) -> str:
        """Look up saved user memory facts."""
        uid = user_id or getattr(self.ctx.proc, "userdata", {}).get(
            "user_id", "riya_verma"
        )
        logger.info(f"TOOL CALL: lookup_user_memory (user_id='{uid}')")
        res = await fn_lookup_user_memory(context, user_id=uid)
        return res

    @function_tool
    async def save_user_memory(
        self,
        context: RunContext,
        name: Optional[str] = None,
        language_preference: Optional[str] = None,
        ongoing_conditions: Optional[list] = None,
        last_triage_outcome: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Save user health memory facts."""
        uid = user_id or getattr(self.ctx.proc, "userdata", {}).get(
            "user_id", "riya_verma"
        )
        logger.info(f"TOOL CALL: save_user_memory (name='{name}', user_id='{uid}')")
        res = await fn_save_user_memory(
            context,
            name=name or "",
            language_preference=language_preference or "",
            ongoing_conditions=ongoing_conditions,
            last_triage_outcome=last_triage_outcome or "",
            user_id=uid,
        )
        return res

    @function_tool
    async def forget_my_data(
        self,
        context: RunContext,
        user_id: Optional[str] = None,
    ) -> str:
        """Delete saved user health memory after explicit user confirmation."""
        uid = user_id or getattr(self.ctx.proc, "userdata", {}).get(
            "user_id", "riya_verma"
        )
        logger.info(f"TOOL CALL: forget_my_data (user_id='{uid}')")
        res = await fn_forget_my_data(context, user_id=uid)
        return res

    @function_tool
    async def what_do_you_remember(
        self,
        context: RunContext,
        user_id: Optional[str] = None,
    ) -> str:
        """Summarize saved user health memory."""
        uid = user_id or getattr(self.ctx.proc, "userdata", {}).get(
            "user_id", "riya_verma"
        )
        res = await fn_what_do_you_remember(context, user_id=uid)
        return res

    @function_tool
    async def end_call(
        self,
        context: RunContext,
        reason: Optional[str] = None,
    ) -> str:
        """End the outbound call session cleanly when user asks to stop, declines, or finishes follow-up."""
        reason = reason or "DECLINED"
        logger.info(f"TOOL CALL: end_call (reason='{reason}')")
        call_id = getattr(self.ctx.proc, "userdata", {}).get(
            "call_id", self.ctx.room.name
        )
        OutboundCallService.update_call_status(call_id=call_id, status=reason.lower())
        await self._hangup()
        return f"Outbound call ended cleanly ({reason})."

    async def _hangup(self) -> None:
        """Delete room to drop SIP leg cleanly."""
        try:
            await self.ctx.api.room.delete_room(
                api.DeleteRoomRequest(room=self.ctx.room.name)
            )
        except Exception as e:
            logger.warning(f"Error closing room on hangup: {e}")


# Use PROCESS executor so Silero VAD inference runs in a subprocess and does NOT
# block the asyncio event loop — prevents turn-detector TimeoutErrors and high latency.
server = AgentServer(job_executor_type=JobExecutorType.PROCESS)


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load(
        # Raised activation_threshold to 0.5 (default) to reduce false VAD triggers;
        # min_silence_duration lowered to 0.2s to end turns faster without waiting.
        min_speech_duration=0.1,
        min_silence_duration=0.2,
        prefix_padding_duration=0.2,
        activation_threshold=0.5,
    )
    init_db()

    # Launch HTTP API Server on the main event loop
    try:
        try:
            from src.api_server import start_api_server
        except ImportError:
            from api_server import start_api_server

        loop = asyncio.get_event_loop()
        _api_server_task = loop.create_task(
            start_api_server(host="127.0.0.1", port=8000)
        )
        proc.userdata["api_server_task"] = _api_server_task
        logger.info(
            "[API Server] Outbound HTTP API Server running at http://127.0.0.1:8000"
        )

    except Exception as e:
        logger.debug(f"[API Server Prewarm Notice]: {e}")


server.setup_fnc = prewarm


def parse_job_metadata(ctx: JobContext) -> dict:
    """Parse phone_number, user_id, and name from job metadata."""
    metadata = ctx.job.metadata or ""
    if not metadata:
        return {}
    try:
        return json.loads(metadata)
    except json.JSONDecodeError:
        return {"phone_number": metadata.strip()}


@server.rtc_session(agent_name="outbound-agent")
async def outbound_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    meta = parse_job_metadata(ctx)

    phone_number = (
        meta.get("phone_number") or meta.get("phone") or meta.get("phoneNumber")
    )
    user_id = meta.get("user_id") or meta.get("userId") or "riya_verma"
    user_name = meta.get("name") or meta.get("user_name") or "Riya"
    call_id = meta.get("call_id") or ctx.room.name

    ctx.proc.userdata["user_id"] = user_id
    ctx.proc.userdata["call_id"] = call_id

    # Pre-fetch user memory facts for smooth prompt customization
    if user_id:
        prefetch_task = asyncio.create_task(
            asyncio.to_thread(MemoryService.get_memory, user_id)
        )
        ctx.proc.userdata["prefetch_task"] = prefetch_task

    # Build HealthSaathi outbound prompt
    mem = MemoryService.get_memory(user_id)
    summary_str = MemoryService.format_memory_summary(mem)
    instructions = build_outbound_instructions(
        user_name_or_context=user_name, user_context_str=summary_str
    )

    # LLM Initialization: Multi-provider support (OpenRouter -> NVIDIA -> Groq -> Google Gemini)
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    google_key = os.getenv("GOOGLE_API_KEY", "").strip()

    if provider == "openrouter" or (not provider and openrouter_key):
        openrouter_model = os.getenv(
            "OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct"
        ).strip()
        logger.info(f"[LLM] OpenRouter ({openrouter_model})")
        llm = openai.LLM(
            model=openrouter_model,
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            temperature=0.7,
            parallel_tool_calls=False,
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        )
    elif provider == "nvidia" or (not provider and nvidia_key):
        nvidia_model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct").strip()
        nvidia_base_url = os.getenv(
            "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
        ).strip()
        logger.info(f"[LLM] NVIDIA NIM API ({nvidia_model})")
        llm = openai.LLM(
            model=nvidia_model,
            base_url=nvidia_base_url,
            api_key=nvidia_key,
            temperature=0.7,
            top_p=1.0,
            parallel_tool_calls=False,
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        )
    elif provider == "groq" or (not provider and groq_key):
        groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        logger.info(f"[LLM] Groq API ({groq_model})")
        llm = openai.LLM(
            model=groq_model,
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
            temperature=0.7,
            parallel_tool_calls=False,
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        )
    elif provider == "google" or (not provider and google_key):
        logger.info("[LLM] Google Gemini (gemini-2.0-flash)")
        llm = google.LLM(model="gemini-2.0-flash")
    else:
        logger.info("[LLM] Google Gemini (gemini-2.0-flash) default")
        llm = google.LLM(model="gemini-2.0-flash")

    tts_transforms = ["filter_markdown", "filter_emoji"]

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi", smart_format=True),
        llm=llm,
        tts=murf.TTS(
            model="falcon",
            voice="Samar",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
        ),
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
        # Tightened endpointing: respond sooner after silence, cap wait at 5s.
        # This reduces the perceived lag between user speech and agent reply.
        min_endpointing_delay=0.2,
        max_endpointing_delay=5.0,
        preemptive_generation=True,
        tts_text_transforms=tts_transforms,
        user_away_timeout=8.0,
        userdata={"user_id": user_id},
    )

    t_stt_final = 0.0

    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev):
        nonlocal t_stt_final
        if getattr(ev, "is_final", False):
            t_stt_final = time.perf_counter()
            _prune_history(session, max_turns=6)
            transcript = getattr(ev, "transcript", "") or str(ev)
            logger.info(f"[Outbound Agent STT]: '{transcript}'")

    @session.on("agent_state_changed")
    def _on_agent_state_changed(ev):
        nonlocal t_stt_final
        new_state = getattr(ev, "new_state", "")
        old_state = getattr(ev, "old_state", "")
        if new_state == "speaking":
            if t_stt_final > 0:
                elapsed_ms = (time.perf_counter() - t_stt_final) * 1000.0
                logger.info(f"[Latency] End speech -> first audio: {elapsed_ms:.1f} ms")
            logger.info("[Outbound Agent TTS]: Generating speech...")
        elif old_state == "speaking" and new_state == "listening":
            logger.info("[Outbound Agent TTS]: Audio playback complete")

    @session.on("user_state_changed")
    def _on_user_state_changed(ev):
        new_state = getattr(ev, "new_state", "")
        if new_state == "away":
            logger.info("USER SILENT (8s timeout) -> Auto-generating check-in prompt")
            session.generate_reply(
                instructions="The user has been quiet. Gently check in: 'Is this still a good time for your health follow-up?'"
            )

    @session.on("error")
    def _on_session_error(err):
        logger.error(f"[Outbound Agent Session Error]: {err}")

    greeting_text = f"Namaste, this is HealthSaathi. I'm calling for a quick health follow-up. Am I speaking with {user_name}?"

    await ctx.connect()

    assistant = HealthSaathiOutboundAgent(
        ctx=ctx, instructions=instructions, initial_greeting=greeting_text
    )

    # Dial SIP participant if phone_number is provided and no remote participant exists yet
    if phone_number and not ctx.room.remote_participants:
        trunk_id = (
            os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID", "").strip()
            or os.getenv("LIVEKIT_SIP_TRUNK_ID", "").strip()
        )

        clean_call_to = phone_number.strip()
        if clean_call_to.lower().startswith("sip:"):
            clean_call_to = clean_call_to[4:]
        if "@" in clean_call_to:
            clean_call_to = clean_call_to.split("@")[0]

        linphone_user = (
            os.getenv("LINPHONE_USERNAME", "").strip()
            or os.getenv("SIP_USERNAME", "").strip()
        )
        clean_sip_number = linphone_user
        if clean_sip_number.lower().startswith("sip:"):
            clean_sip_number = clean_sip_number[4:]
        if "@" in clean_sip_number:
            clean_sip_number = clean_sip_number.split("@")[0]

        async def _dial_sip():
            logger.info(
                f"Dialing SIP target '{clean_call_to}' for user '{user_id}' (From: '{clean_sip_number}')..."
            )
            try:
                req_kwargs = {
                    "room_name": ctx.room.name,
                    "sip_trunk_id": trunk_id,
                    "sip_call_to": clean_call_to,
                    "participant_identity": CALLEE_IDENTITY,
                    "participant_name": user_name or f"User_{user_id}",
                    "wait_until_answered": True,
                    "media_encryption": api.SIPMediaEncryption.SIP_MEDIA_ENCRYPT_ALLOW,
                }
                if clean_sip_number:
                    req_kwargs["sip_number"] = clean_sip_number

                await ctx.api.sip.create_sip_participant(
                    api.CreateSIPParticipantRequest(**req_kwargs)
                )
                OutboundCallService.update_call_status(
                    call_id=call_id, status="connected"
                )
            except Exception as e:
                logger.error(f"Outbound SIP call to {clean_call_to} failed: {e}")
                OutboundCallService.update_call_status(call_id=call_id, status="failed")

        dial_task = asyncio.create_task(_dial_sip())
        ctx.proc.userdata["dial_task"] = dial_task

    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )


if __name__ == "__main__":
    cli.run_app(server)
