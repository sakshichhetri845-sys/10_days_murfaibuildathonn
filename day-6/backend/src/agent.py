import logging
import os
from typing import Optional

import aiohttp
import httpx
from dotenv import load_dotenv
from livekit import rtc

# pyrefly: ignore [missing-import]
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
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
    from src.memory_service import MemoryService
    from src.memory_tools import (
        end_call,
        forget_my_data,
        lookup_user_memory,
        save_user_memory,
        what_do_you_remember,
    )
    from src.prompts.outbound_prompt import build_outbound_instructions
    from src.prompts.system_prompt import SYSTEM_PROMPT
except ImportError:
    from memory_service import MemoryService
    from memory_tools import (
        end_call,
        forget_my_data,
        lookup_user_memory,
        save_user_memory,
        what_do_you_remember,
    )
    from prompts.outbound_prompt import build_outbound_instructions
    from prompts.system_prompt import SYSTEM_PROMPT


async def _check_nvidia_available(api_key: str, model: str) -> bool:
    """Check that the configured NVIDIA NIM model can accept a chat request."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1,
                },
            )
            if resp.status_code != 200:
                logger.warning(
                    "[LLM] NVIDIA NIM returned %s — switching to Gemini",
                    resp.status_code,
                )
                return False
            return True
    except Exception as e:
        logger.warning(
            "[LLM] NVIDIA NIM health check failed: %s — switching to Gemini", e
        )
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
            return f"Hi {name}, this is BolBuddy, your English practice companion. You scheduled your daily practice call for now. Is this a good time to practice for a few minutes?"
    except Exception as e:
        logger.warning(f"Could not load memory for greeting: {e}")
    return "Hi there, this is BolBuddy, your English practice companion. You scheduled your daily practice call for now. Is this a good time to practice for a few minutes?"


class Assistant(Agent):
    def __init__(
        self,
        initial_greeting: str = "Namaste! I am HealthSaathi, your voice health guide. How can I help you today?",
        instructions: Optional[str] = None,
    ) -> None:

        super().__init__(
            instructions=instructions or SYSTEM_PROMPT,
            tools=[
                lookup_user_memory,
                save_user_memory,
                forget_my_data,
                what_do_you_remember,
                end_call,
            ],
        )
        self._initial_greeting = initial_greeting

    async def on_enter(self) -> None:
        """Speak the personalised greeting as soon as the agent joins."""
        await self.session.say(self._initial_greeting, allow_interruptions=True)


server = AgentServer()


_api_server_started = False


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext) -> None:
    global _api_server_started
    if not _api_server_started:
        _api_server_started = True
        try:
            import asyncio

            from src.api_server import start_api_server

            ctx.proc.userdata["api_server_task"] = asyncio.create_task(
                start_api_server(host="127.0.0.1", port=8000)
            )
            logger.info(
                "[API Server] Outbound HTTP API Server running at http://127.0.0.1:8000"
            )

        except Exception as api_err:
            logger.warning(f"[API Server] Could not start API server: {api_err}")

    ctx.log_context_fields = {"room": ctx.room.name}

    # --- connect first so participants are visible ---
    await ctx.connect()

    # --- resolve stable user_id from the connected room ---
    user_id = "anonymous_user"
    if ctx.room and ctx.room.remote_participants:
        p = next(iter(ctx.room.remote_participants.values()), None)
        if p and p.identity:
            user_id = p.identity

    # --- Day 6 Outbound Session Detection ---
    room_name = ctx.room.name if ctx.room else ""
    is_outbound = room_name.startswith("outbound-") or room_name.startswith("followup-")

    if is_outbound:
        logger.info("[DAY6] Outbound follow-up detected")

        # Resolve user_id from room name (e.g. outbound-followup-riya_verma -> riya_verma)
        clean_id = room_name
        for prefix in ["outbound-followup-", "outbound-", "followup-"]:
            if clean_id.startswith(prefix):
                clean_id = clean_id[len(prefix) :]
                break

        if clean_id and clean_id != room_name:
            user_id = clean_id

        logger.info(f"[DAY6] Loading memory for user: {user_id}")
        memory = MemoryService.get_memory(user_id)

        if memory:
            logger.info("[DAY6] Previous interaction loaded")
            context_str = MemoryService.format_memory_summary(memory)
            name = memory.get("name", "")
            if name:
                initial_greeting = (
                    f"Hello {name}, this is HealthSaathi, an automated health assistant. "
                    "I'm calling for a quick follow-up regarding your previous health inquiry. "
                    "If now isn't a good time, that's completely okay—you can end the call at any time. "
                    "Would you like to continue?"
                )
            else:
                initial_greeting = (
                    "Hello, this is HealthSaathi, an automated health assistant. "
                    "I'm calling for a quick follow-up regarding your previous health inquiry. "
                    "If now isn't a good time, that's completely okay—you can end the call at any time. "
                    "Would you like to continue?"
                )
        else:
            context_str = (
                "No prior interaction recorded for this user. "
                "Perform a generic follow-up without inventing previous medical details."
            )
            initial_greeting = (
                "Hello, this is HealthSaathi, an automated health assistant. "
                "I'm calling for a quick follow-up regarding your health inquiry. "
                "If now isn't a good time, that's completely okay—you can end the call at any time. "
                "Would you like to continue?"
            )

        logger.info("[DAY6] Starting HealthSaathi follow-up")
        instructions = build_outbound_instructions(context_str)
    else:
        logger.info(f"[memory] resolved user_id={user_id}")
        initial_greeting = _build_greeting(user_id)
        instructions = SYSTEM_PROMPT

    # --- LLM selection: OpenRouter primary (fastest for voice), NVIDIA NIM secondary, Gemini tertiary ---
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()

    if (provider == "openrouter" or not provider) and openrouter_key:
        openrouter_model = os.getenv(
            "OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct"
        ).strip()
        logger.info("[LLM] OpenRouter %s — Primary Voice Agent LLM", openrouter_model)
        llm = openai.LLM(
            model=openrouter_model,
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            temperature=0.7,
            parallel_tool_calls=False,
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        )
    elif nvidia_key:
        nvidia_model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct").strip()
        logger.info("[LLM] NVIDIA NIM %s — Secondary LLM", nvidia_model)
        llm = openai.LLM(
            model=nvidia_model,
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_key,
            temperature=0.7,
            parallel_tool_calls=False,
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        )
    else:
        logger.info("[LLM] Google Gemini 2.0 Flash — Fallback LLM")
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
        agent=Assistant(initial_greeting=initial_greeting, instructions=instructions),
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
