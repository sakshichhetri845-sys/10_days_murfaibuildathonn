import logging
import os

import aiohttp
import httpx
from dotenv import load_dotenv
from livekit import rtc

# pyrefly: ignore [missing-import]
from livekit.agents import (
    Agent,
    AgentSession,
    AgentServer,
    JobContext,
    JobProcess,
    cli,
    room_io,
    tokenize,
)

# pyrefly: ignore [missing-import]
from livekit.plugins import deepgram, google, murf, noise_cancellation, openai, silero

# pyrefly: ignore [missing-import]
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

try:
    from src.memory_tools import (
        forget_my_data,
        lookup_user_memory,
        save_user_memory,
        what_do_you_remember,
    )
    from src.memory_service import MemoryService
    from src.prompts.system_prompt import SYSTEM_PROMPT
except ImportError:
    from memory_tools import (
        forget_my_data,
        lookup_user_memory,
        save_user_memory,
        what_do_you_remember,
    )
    from memory_service import MemoryService
    from prompts.system_prompt import SYSTEM_PROMPT


async def _check_groq_available() -> bool:
    """
    Check Groq availability. Returns False if rate-limited or unreachable.
    Checks the actual remaining token budget to avoid mid-session failures.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('GROQ_API_KEY', '')}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1,
                },
            )
            if resp.status_code == 429:
                logger.warning("[LLM] Groq rate limit hit — switching to Gemini")
                return False
            if resp.status_code != 200:
                logger.warning(f"[LLM] Groq returned {resp.status_code} — switching to Gemini")
                return False
            # Check remaining daily token budget from response headers
            remaining = resp.headers.get("x-ratelimit-remaining-tokens-day", "")
            if remaining and int(remaining) < 5000:
                logger.warning(f"[LLM] Groq daily tokens low ({remaining} left) — switching to Gemini")
                return False
            return True
    except Exception as e:
        logger.warning(f"[LLM] Groq health check failed: {e} — switching to Gemini")
        return False


def _build_greeting(user_id: str) -> str:
    """
    Look up memory for this user and return a personalised opening line.
    Falls back to a generic greeting for new users.
    The greeting must match the tone defined in the system prompt.
    """
    try:
        memory = MemoryService.get_memory(user_id)
        if memory and memory.get("name"):
            name = memory["name"]
            last = memory.get("last_triage_outcome", "")
            if last:
                return (
                    f"Welcome back, {name}. Last time, we discussed a health concern — "
                    f"{last}. How are you feeling today?"
                )
            return f"Welcome back, {name}. How can I help you today?"
    except Exception as e:
        logger.warning(f"Could not load memory for greeting: {e}")
    return "Namaste! I'm HealthSathi. How can I help you today?"


class Assistant(Agent):
    def __init__(self, initial_greeting: str) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            tools=[
                lookup_user_memory,
                save_user_memory,
                forget_my_data,
                what_do_you_remember,
            ],
        )
        self._initial_greeting = initial_greeting

    async def on_enter(self) -> None:
        """Speak the personalised greeting as soon as the agent joins."""
        await self.session.say(self._initial_greeting, allow_interruptions=True)


server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}

    # --- connect first so participants are visible ---
    await ctx.connect()

    # --- resolve stable user_id from the connected room ---
    user_id = "anonymous_user"
    if ctx.room and ctx.room.remote_participants:
        p = next(iter(ctx.room.remote_participants.values()), None)
        if p and p.identity:
            user_id = p.identity
    logger.info(f"[memory] resolved user_id={user_id}")

    # --- build personalised greeting from memory (sync, safe) ---
    initial_greeting = _build_greeting(user_id)

    # --- LLM selection: Groq primary when available, Gemini fallback ---
    groq_key = os.getenv("GROQ_API_KEY")
    groq_available = False
    if groq_key:
        groq_available = await _check_groq_available()

    if groq_available:
        logger.info("[LLM] Groq llama-3.3-70b-versatile — primary")
        llm = openai.LLM(
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
            model="llama-3.3-70b-versatile",
        )
    else:
        logger.info("[LLM] Groq unavailable/rate-limited — Google Gemini 2.0 Flash fallback")
        llm = google.LLM(model="gemini-2.0-flash")

    # --- aiohttp session for Murf TTS, cleaned up on job end ---
    http_session = aiohttp.ClientSession()
    ctx.add_shutdown_callback(http_session.close)

    # --- voice pipeline ---
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=llm,
        tts=murf.TTS(
            voice="Samar",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
            http_session=http_session,
        ),
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
        preemptive_generation=True,
        # Pass user_id via userdata so memory tools can resolve it from RunContext
        userdata={"user_id": user_id},
    )

    # Keep userdata in sync if a new participant joins mid-session
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant) -> None:
        logger.info(f"Participant connected: identity={participant.identity}")
        if participant.identity:
            session.userdata["user_id"] = participant.identity

    # --- start the session ---
    await session.start(
        agent=Assistant(initial_greeting=initial_greeting),
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
