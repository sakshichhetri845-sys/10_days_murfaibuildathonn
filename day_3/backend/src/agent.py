import logging
import os

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

# System prompt is modularized in src/prompts/system_prompt.py
try:
    # pyrefly: ignore [missing-import]
    from src.prompts.system_prompt import SYSTEM_PROMPT
except ImportError:
    from prompts.system_prompt import SYSTEM_PROMPT


async def _check_groq_available() -> bool:
    """Quick health check: can we reach the Groq API from this network?"""
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
            return resp.status_code == 200
    except Exception as e:
        logger.warning(f"Groq health check failed: {e}")
        return False


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Try Groq first, fall back to Google Gemini if Groq is unreachable
    if await _check_groq_available():
        logger.info(
            "✅ Groq API is reachable — using Groq LLM (llama-3.3-70b-versatile)"
        )
        llm = openai.LLM(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY") or "",
            model="llama-3.3-70b-versatile",
        )
    else:
        logger.info("⚠️ Groq API unreachable — falling back to Google Gemini 2.0 Flash")
        llm = google.LLM(model="gemini-2.0-flash")

    # Set up a voice AI pipeline matching official Murf multilingual recommendation
    session = AgentSession(
        # Speech-to-text (STT) with multilingual support ("multi" set to detect non-english transcripts)
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        llm=llm,
        # Text-to-speech (TTS) via Murf Falcon (voice="Anisha" with locale key NOT hardcoded to avoid foreign accent)
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        # Multilingual turn detection for seamless speech pauses in Hindi, Hinglish & English
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
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

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
