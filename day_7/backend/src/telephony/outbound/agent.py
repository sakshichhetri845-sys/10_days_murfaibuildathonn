"""
BolBuddy Outbound Telephony Agent — Day 6 Voice Agent.

Initiates daily English practice calls at the learner's chosen time.
Integrates BolBuddy's complete voice pipeline:
- Deepgram Nova-3 Multilingual STT (en + hi + hinglish)
- Primary NVIDIA LLM (with Google Gemini fallback)
- Murf Falcon TTS (voice="Anisha")
- Silero VAD + LiveKit Agents SDK (~1.4)
- Persistent Memory (db.py & memory_tools.py)
- Call outcome logging (outbound.py)
"""

import asyncio
import json
import logging
import os
import sys

import httpx
from dotenv import load_dotenv
from livekit import api
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    tokenize,
)
from livekit.agents.job import JobExecutorType
from livekit.plugins import deepgram, google, murf, openai, silero

# Add backend/src to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from db import get_user, init_db
from exercises import get_next_exercise as fn_get_next_exercise
from memory_tools import (
    async_prefetch_user_memory,
)
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
from outbound import record_call_outcome
from prompts.system_prompt import SYSTEM_PROMPT
from rag import search_learning_resources as fn_search_learning_resources
from scoring import score_spoken_answer as fn_score_spoken_answer

logger = logging.getLogger("bolbuddy.outbound_agent")
load_dotenv(".env.local")

OUTBOUND_TRUNK_ID = (
    os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID", "").strip()
    or os.getenv("LIVEKIT_SIP_TRUNK_ID", "").strip()
)
CALLEE_IDENTITY = "phone-user"


class BolBuddyOutboundAgent(Agent):
    def __init__(self, ctx: JobContext) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.ctx = ctx

    @function_tool
    async def lookup_user_memory(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Look up saved user memory facts. Use only when needed to retrieve saved memory."""
        uid = user_id or getattr(self.ctx.proc, "userdata", {}).get(
            "user_id", "default_user"
        )
        logger.info(f"TOOL CALL: lookup_user_memory (user_id='{uid}')")
        res = await fn_lookup_user_memory(context, user_id=uid)
        logger.info("TOOL COMPLETE: lookup_user_memory")
        return res

    @function_tool
    async def save_user_memory(
        self,
        context: RunContext,
        name: str = "",
        language_preference: str = "",
        level: str = "",
        learning_goal: str = "",
        topic_practiced: str = "",
        recurring_challenge: str = "",
        user_id: str = "",
    ) -> str:
        """Save user memory facts (name, level, goal, challenge)."""
        uid = user_id or getattr(self.ctx.proc, "userdata", {}).get(
            "user_id", "default_user"
        )
        logger.info(f"TOOL CALL: save_user_memory (name='{name}', user_id='{uid}')")
        res = await fn_save_user_memory(
            context,
            name=name,
            language_preference=language_preference,
            level=level,
            learning_goal=learning_goal,
            topic_practiced=topic_practiced,
            recurring_challenge=recurring_challenge,
            user_id=uid,
        )
        return res

    @function_tool
    async def forget_my_data(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Delete saved user memory after explicit user confirmation."""
        uid = user_id or getattr(self.ctx.proc, "userdata", {}).get(
            "user_id", "default_user"
        )
        logger.info(f"TOOL CALL: forget_my_data (user_id='{uid}')")
        res = await fn_forget_my_data(context, user_id=uid)
        return res

    @function_tool
    async def what_do_you_remember(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Summarize saved user memory."""
        uid = user_id or getattr(self.ctx.proc, "userdata", {}).get(
            "user_id", "default_user"
        )
        res = await fn_what_do_you_remember(context, user_id=uid)
        return res

    @function_tool
    async def search_learning_resources(
        self,
        context: RunContext,
        query: str = "",
    ) -> str:
        """Search learning resources for grammar rules, viva tips, or interview prep."""
        res = await fn_search_learning_resources(context, query=query)
        return res

    @function_tool
    async def fetch_next_exercise(
        self,
        context: RunContext,
        level: str = "beginner",
        topic: str = "interview",
    ) -> str:
        """Return one speaking exercise for requested level and topic."""
        res_dict = fn_get_next_exercise(level=level, topic=topic)
        return json.dumps(res_dict)

    @function_tool
    async def score_spoken_answer(
        self,
        context: RunContext,
        question: str = "",
        answer: str = "",
        transcript: str = "",
        practice_topic: str = "",
    ) -> str:
        """Evaluate a completed spoken answer."""
        res = await fn_score_spoken_answer(
            context,
            question=question,
            answer=answer,
            transcript=transcript,
            practice_topic=practice_topic,
        )
        return res

    async def detected_answering_machine(self) -> str:
        """Internal helper to log voicemail and hang up when an automated machine is detected."""
        logger.info("Answering machine detected — hanging up and recording outcome")
        call_id = getattr(self.ctx.proc, "userdata", {}).get(
            "call_id", self.ctx.room.name
        )
        record_call_outcome(call_id, "VOICEMAIL")
        await self._hangup()
        return "Voicemail detected. Call ended."

    @function_tool
    async def end_call(
        self,
        context: RunContext,
        reason: str = "DECLINED",
    ) -> str:
        """End the outbound call session cleanly ONLY when the learner explicitly says goodbye, declines to practice, or requests to disconnect."""
        logger.info(f"TOOL CALL: end_call (reason='{reason}')")
        call_id = getattr(self.ctx.proc, "userdata", {}).get(
            "call_id", self.ctx.room.name
        )
        record_call_outcome(call_id, reason.upper())
        await self._hangup()
        return f"Call ended gracefully ({reason})."

    async def _hangup(self) -> None:
        """Delete room to drop SIP leg cleanly."""
        try:
            await self.ctx.api.room.delete_room(
                api.DeleteRoomRequest(room=self.ctx.room.name)
            )
        except Exception as e:
            logger.warning(f"Error closing room on hangup: {e}")


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
    """Sanitize spoken text output to ensure no raw tool tags, XML, or JSON reach TTS audio synthesis."""
    if not text:
        return ""
    import re

    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\{[\s\S]*?\}", "", text)
    text = re.sub(r"function\s*[:=]?\s*\w+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[`*_~#]", "", text)
    return re.sub(r"\s+", " ", text).strip()


server = AgentServer(job_executor_type=JobExecutorType.THREAD)


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=0.2,
        prefix_padding_duration=0.2,
        activation_threshold=0.3,
    )
    init_db()


server.setup_fnc = prewarm


def parse_job_metadata(ctx: JobContext) -> dict:
    """Parse phone number, user_id, and name from job metadata."""
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
    phone_number = meta.get("phone_number") or meta.get("phone")
    user_id = meta.get("user_id") or meta.get("userId") or "default_user"
    user_name = meta.get("name") or meta.get("user_name") or ""
    call_id = meta.get("call_id") or ctx.room.name

    ctx.proc.userdata["user_id"] = user_id
    ctx.proc.userdata["call_id"] = call_id

    if not phone_number:
        logger.error("No phone_number found in job metadata.")
        record_call_outcome(
            call_id, "PROVIDER_ERROR", details="Missing destination phone number."
        )
        ctx.shutdown()
        return

    trunk_id = (
        os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID", "").strip()
        or os.getenv("LIVEKIT_SIP_TRUNK_ID", "").strip()
    )

    if not trunk_id or "ST_your_sip_trunk_id" in trunk_id:
        logger.error(
            "LIVEKIT_SIP_OUTBOUND_TRUNK_ID is not configured in environment. "
            "Please set LIVEKIT_SIP_OUTBOUND_TRUNK_ID=ST_your_real_trunk_id in backend/.env.local"
        )
        record_call_outcome(
            call_id,
            "PROVIDER_ERROR",
            details="Missing LIVEKIT_SIP_OUTBOUND_TRUNK_ID in backend/.env.local",
        )
        ctx.shutdown()
        return

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
        logger.info(f"LLM Provider: OpenRouter ({openrouter_model})")
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
        logger.info(f"LLM Provider: NVIDIA API ({nvidia_model})")
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
        logger.info(f"LLM Provider: Groq API ({groq_model})")
        llm = openai.LLM(
            model=groq_model,
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
            temperature=0.7,
            parallel_tool_calls=False,
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        )
    elif provider == "google" or (not provider and google_key):
        logger.info("LLM Provider: Google Gemini (gemini-2.0-flash)")
        llm = google.LLM(model="gemini-2.0-flash")
    else:
        raise ValueError(
            "No valid LLM API key (OpenRouter, NVIDIA, Groq, or Google) found in environment."
        )

    tts_transforms = ["filter_markdown", "filter_emoji"]

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi", smart_format=True),
        llm=llm,
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
            text_pacing=False,
        ),
        vad=ctx.proc.userdata["vad"],
        min_endpointing_delay=0.15,
        max_endpointing_delay=0.5,
        preemptive_generation=True,
        tts_text_transforms=tts_transforms,
        user_away_timeout=8.0,
    )

    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev):
        if getattr(ev, "is_final", False):
            _prune_history(session, max_turns=6)
            transcript = getattr(ev, "transcript", "") or str(ev)
            logger.info(f"USER SPOKE (STT TRANSCRIPT): '{transcript}'")
            logger.info("LLM GENERATION STARTING...")

    @session.on("agent_state_changed")
    def _on_agent_state_changed(ev):
        new_state = getattr(ev, "new_state", "")
        old_state = getattr(ev, "old_state", "")
        if new_state == "speaking":
            logger.info("LLM GENERATION COMPLETE -> MURF TTS AUDIO STARTING...")
        elif old_state == "speaking" and new_state == "listening":
            logger.info("MURF TTS AUDIO PLAYBACK COMPLETE")

    @session.on("user_state_changed")
    def _on_user_state_changed(ev):
        new_state = getattr(ev, "new_state", "")
        if new_state == "away":
            logger.info(
                "USER SILENT (8s timeout) -> Auto-generating conversation continuation prompt"
            )
            session.generate_reply(
                instructions="The learner has been quiet for a few seconds. Gently check in and ask an encouraging question to keep the English practice conversation flowing."
            )

    @session.on("error")
    def _on_session_error(err):
        logger.error(f"VOICE SESSION ERROR DETECTED: {err}")

    await ctx.connect()

    session_started = asyncio.create_task(
        session.start(
            agent=BolBuddyOutboundAgent(ctx),
            room=ctx.room,
        )
    )
    ctx.proc.userdata["session_task"] = session_started

    linphone_user = (
        os.getenv("LINPHONE_USERNAME", "").strip()
        or os.getenv("SIP_USERNAME", "").strip()
    )
    raw_caller_id = (
        linphone_user
        or os.getenv("LINPHONE_CALLER_ID", "").strip()
        or os.getenv("SIP_CALLER_ID", "").strip()
        or os.getenv("TWILIO_PHONE_NUMBER", "").strip()
        or os.getenv("SIP_NUMBER", "").strip()
    )
    clean_sip_number = raw_caller_id
    if clean_sip_number.lower().startswith("sip:"):
        clean_sip_number = clean_sip_number[4:]
    if "@" in clean_sip_number:
        clean_sip_number = clean_sip_number.split("@")[0]

    # Clean phone_number/sip_call_to: LiveKit expects just the phone number or SIP username (e.g. 'sakshyam' or '+977...'), not a full SIP URI.
    clean_call_to = phone_number.strip()
    if clean_call_to.lower().startswith("sip:"):
        clean_call_to = clean_call_to[4:]
    if "@" in clean_call_to:
        clean_call_to = clean_call_to.split("@")[0]

    logger.info(
        f"Dialing '{clean_call_to}' for user '{user_id}' (From: '{clean_sip_number}')..."
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
        record_call_outcome(call_id, "CONNECTED", user_id=user_id)
    except api.TwirpError as e:
        logger.error(f"Outbound call to {clean_call_to} failed/unanswered: {e}")
        record_call_outcome(call_id, "NO_ANSWER", user_id=user_id, details=str(e))
        session_started.cancel()
        ctx.shutdown()
        return

    # Pre-fetch user memory facts
    prefetch_task = asyncio.create_task(async_prefetch_user_memory(user_id))
    ctx.proc.userdata["prefetch_task"] = prefetch_task

    # Look up user profile name if available
    user_record = get_user(user_id)
    learner_name = user_name or (user_record.get("name") if user_record else None)

    if learner_name:
        greeting_text = (
            f"Hi {learner_name}, this is BolBuddy. I'm calling for your English practice session. "
            f"Is now a good time? If not, you can simply say no and I'll end the call."
        )
    else:
        greeting_text = (
            "Hi, this is BolBuddy. I'm calling for your English practice session. "
            "Is now a good time? If not, you can simply say no and I'll end the call."
        )

    await session.say(_clean_tts_text(greeting_text), allow_interruptions=True)

    # Keep outbound_agent entrypoint active until session completes
    await session_started


if __name__ == "__main__":
    cli.run_app(server)
