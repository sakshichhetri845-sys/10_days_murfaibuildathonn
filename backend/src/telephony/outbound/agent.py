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
from livekit.agents.voice.transcription.filters import TextTransforms
from livekit.plugins import deepgram, google, murf, noise_cancellation, openai, silero

# Add backend/src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db import get_or_create_user, get_user, init_db
from exercises import get_next_exercise as fn_get_next_exercise
from memory_tools import (
    async_prefetch_user_memory,
    forget_my_data as fn_forget_my_data,
    lookup_user_memory as fn_lookup_user_memory,
    save_user_memory as fn_save_user_memory,
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
        logger.info("TOOL CALL: lookup_user_memory")
        res = await fn_lookup_user_memory(context, user_id=user_id)
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
        logger.info(f"TOOL CALL: save_user_memory (name='{name}')")
        res = await fn_save_user_memory(
            context,
            name=name,
            language_preference=language_preference,
            level=level,
            learning_goal=learning_goal,
            topic_practiced=topic_practiced,
            recurring_challenge=recurring_challenge,
            user_id=user_id,
        )
        return res

    @function_tool
    async def forget_my_data(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Delete saved user memory after explicit user confirmation."""
        logger.info(f"TOOL CALL: forget_my_data (user_id='{user_id}')")
        res = await fn_forget_my_data(context, user_id=user_id)
        return res

    @function_tool
    async def what_do_you_remember(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Summarize saved user memory."""
        res = await fn_what_do_you_remember(context, user_id=user_id)
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

    @function_tool
    async def detected_answering_machine(self, context: RunContext) -> str:
        """Hang up cleanly when voicemail or answering machine is detected."""
        logger.info("Answering machine detected — hanging up and recording outcome")
        call_id = getattr(self.ctx.proc, "userdata", {}).get("call_id", self.ctx.room.name)
        record_call_outcome(call_id, "VOICEMAIL")
        await self._hangup()
        return "Voicemail detected. Call ended."

    @function_tool
    async def end_call(
        self,
        context: RunContext,
        reason: str = "DECLINED",
    ) -> str:
        """End the outbound call session cleanly after user declines or asks to disconnect."""
        logger.info(f"TOOL CALL: end_call (reason='{reason}')")
        call_id = getattr(self.ctx.proc, "userdata", {}).get("call_id", self.ctx.room.name)
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


def _clean_tts_text(text: str) -> str:
    """Sanitize spoken text output for TTS."""
    if not text:
        return ""
    import re

    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\{[\s\S]*?\}", "", text)
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
        record_call_outcome(call_id, "PROVIDER_ERROR", details="Missing destination phone number.")
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

    # LLM Initialization: NVIDIA API Primary Provider
    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
    nvidia_model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct").strip()
    nvidia_base_url = os.getenv(
        "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
    ).strip()

    if nvidia_key:
        logger.info("LLM Provider: NVIDIA API")
        llm = openai.LLM(
            model=nvidia_model,
            base_url=nvidia_base_url,
            api_key=nvidia_key,
            temperature=0.7,
            top_p=1.0,
            timeout=httpx.Timeout(15.0),
        )
    else:
        google_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if google_key:
            logger.info("LLM Fallback Provider: Google Gemini")
            llm = google.LLM(model="gemini-2.0-flash")
        else:
            raise ValueError("NVIDIA_API_KEY or GOOGLE_API_KEY is required.")

    tts_transforms: list[TextTransforms] = ["filter_markdown", "filter_emoji"]

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=llm,
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
            text_pacing=True,
        ),
        vad=ctx.proc.userdata["vad"],
        min_endpointing_delay=0.2,
        max_endpointing_delay=0.8,
        preemptive_generation=False,
        tts_text_transforms=tts_transforms,
    )

    await ctx.connect()

    session_started = asyncio.create_task(
        session.start(
            agent=BolBuddyOutboundAgent(ctx),
            room=ctx.room,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=lambda params: (
                        noise_cancellation.BVCTelephony()
                        if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                        else noise_cancellation.BVC()
                    ),
                ),
            ),
        )
    )

    sip_number = (
        os.getenv("TWILIO_PHONE_NUMBER", "").strip()
        or os.getenv("SIP_CALLER_ID", "").strip()
        or os.getenv("SIP_NUMBER", "").strip()
    )

    logger.info(f"Dialing {phone_number} for user '{user_id}'...")
    try:
        req_kwargs = {
            "room_name": ctx.room.name,
            "sip_trunk_id": trunk_id,
            "sip_call_to": phone_number,
            "participant_identity": CALLEE_IDENTITY,
            "participant_name": user_name or f"User_{user_id}",
            "wait_until_answered": True,
        }
        if sip_number:
            req_kwargs["sip_number"] = sip_number

        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(**req_kwargs)
        )
        record_call_outcome(call_id, "CONNECTED", user_id=user_id)
    except api.TwirpError as e:
        logger.error(f"Outbound call to {phone_number} failed/unanswered: {e}")
        record_call_outcome(call_id, "NO_ANSWER", user_id=user_id, details=str(e))
        session_started.cancel()
        ctx.shutdown()
        return

    await session_started

    # Pre-fetch user memory facts
    prefetch_task = asyncio.create_task(async_prefetch_user_memory(user_id))
    ctx.proc.userdata["prefetch_task"] = prefetch_task

    # Look up user profile name if available
    user_record = get_user(user_id)
    learner_name = user_name or (user_record.get("name") if user_record else None)

    if learner_name:
        greeting_text = (
            f"Hi {learner_name}, this is BolBuddy, your English practice companion. "
            f"You scheduled your daily practice call for this time. If you'd rather not practice now, "
            f"just say so and I'll end the call. Want to practice for a few minutes?"
        )
    else:
        greeting_text = (
            "Hi, this is BolBuddy, your English practice companion. "
            "You scheduled your daily practice call for this time. If you'd rather not practice now, "
            "just say so and I'll end the call. Want to practice for a few minutes?"
        )

    await session.say(greeting_text, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
