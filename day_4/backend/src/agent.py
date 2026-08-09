import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv

# pyrefly: ignore [missing-import]
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
from livekit.agents.voice.transcription.filters import TextTransforms

# pyrefly: ignore [missing-import]
from livekit.plugins import deepgram, google, murf, openai, silero

from db import get_or_create_user, init_db
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
from prompts.system_prompt import SYSTEM_PROMPT
from rag import (
    search_learning_resources as fn_search_learning_resources,
)

logger = logging.getLogger("agent")
load_dotenv(".env.local")


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

    @function_tool
    async def lookup_user_memory(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Look up saved learning memory for the current user, including their name, English level, learning goals, topics practiced, and recurring challenges.

        MANDATORY RESPONSE RULE: Explain what you remember warmly (recalling name and learning goal) AND YOU MUST ALWAYS END YOUR RESPONSE BY EXPLICITLY OFFERING: "If you would ever like me to delete or forget any of your saved details, just let me know!"

        Args:
            context: RunContext provided by LiveKit.
            user_id: Optional user identifier string.
        """
        return await fn_lookup_user_memory(context, user_id=user_id)

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
        """Save or update memory facts for the current user, such as their name, language preference, current level, learning goal, topics practiced, or recurring challenges.

        AUTOMATIC SAVE RULE: Invoke this tool immediately whenever the user shares their name, learning goal, current level, or topic practiced so it is saved to SQLite memory for future calls.

        Args:
            context: RunContext provided by LiveKit.
            name: Learner's preferred name.
            language_preference: Preferred language mode.
            level: English proficiency level.
            learning_goal: Learning goal context (e.g. job interview, college, viva).
            topic_practiced: Topic discussed during practice.
            recurring_challenge: Concise qualitative challenge area.
            user_id: Optional user identifier string.
        """
        return await fn_save_user_memory(
            context,
            name=name,
            language_preference=language_preference,
            level=level,
            learning_goal=learning_goal,
            topic_practiced=topic_practiced,
            recurring_challenge=recurring_challenge,
            user_id=user_id,
        )

    @function_tool
    async def forget_my_data(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Permanently delete or reset all saved memory and learning records for the current user.

        MANDATORY CONFIRMATION RULE: Do NOT invoke this tool unless the user has explicitly confirmed
        their request to delete, reset, clear, or forget their saved memory.

        Args:
            context: RunContext provided by LiveKit.
            user_id: Optional user identifier string.
        """
        return await fn_forget_my_data(context, user_id=user_id)

    @function_tool
    async def what_do_you_remember(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Retrieve and summarize what BolBuddy currently remembers about the user.

        MANDATORY RESPONSE RULE: Explain what you remember warmly (recalling name and learning goal) AND YOU MUST ALWAYS END YOUR RESPONSE BY EXPLICITLY OFFERING: "If you would ever like me to delete or forget any of your saved details, just let me know!"

        Args:
            context: RunContext provided by LiveKit.
            user_id: Optional user identifier string.
        """
        return await fn_what_do_you_remember(context, user_id=user_id)

    @function_tool
    async def search_learning_resources(
        self,
        context: RunContext,
        query: str,
    ) -> str:
        """Search curated English learning resources for grammar rules, viva tips, interview prep, pronunciation, and conversation guidelines.

        Use this tool ONLY when the user explicitly asks a specific conceptual English learning question or requests educational tips (e.g. 'How do I prepare for a viva?').
        DO NOT call this tool for general greetings, small talk, or when asking what the user wants to practice.

        Args:
            context: RunContext provided by LiveKit.
            query: Specific learning question or topic string.
        """
        return await fn_search_learning_resources(context, query=query)


server = AgentServer(job_executor_type=JobExecutorType.THREAD)


def prewarm(proc: JobProcess):
    # Fast noise-resilient VAD with 0.3s silence threshold and 0.5 activation filter
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=0.3,
        prefix_padding_duration=0.2,
        activation_threshold=0.5,
    )
    init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Prefer Groq LLM (llama-3.1-8b-instant) if GROQ_API_KEY is set for 500k TPD quota & sub-150ms voice latency
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if groq_key:
        logger.info("🚀 Using Groq LLM (llama-3.1-8b-instant)")
        llm = openai.LLM(
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
            model="llama-3.1-8b-instant",
        )
    else:
        logger.info("⚡ Using Google Gemini LLM (gemini-2.0-flash)")
        llm = google.LLM(model="gemini-2.0-flash")

    # Built-in text transforms to strip markdown and emojis from spoken audio
    tts_transforms: list[TextTransforms] = ["filter_markdown", "filter_emoji"]

    # Set up a voice AI pipeline matching official Murf multilingual recommendation
    session_kwargs = {
        # Speech-to-text (STT) via Deepgram Nova-3 with multilingual support (en + hi + hinglish)
        "stt": deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) processing user input and executing function tools
        "llm": llm,
        # Text-to-speech (TTS) via Murf Falcon (min_sentence_len=1 for immediate audio streaming)
        "tts": murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
            text_pacing=True,
        ),
        "vad": ctx.proc.userdata["vad"],
        # Fast noise-resilient endpointing delays (0.3s silence threshold, 2.0s max phrase window)
        "min_endpointing_delay": 0.3,
        "max_endpointing_delay": 2.0,
        # Non-preemptive generation to prevent speculative tool execution conflicts
        "preemptive_generation": False,
        "tts_text_transforms": tts_transforms,
    }

    session = AgentSession(**session_kwargs)

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

    # Join the room and connect to the user first
    await ctx.connect()

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )

    # Track user interaction and deliver initial personalized voice greeting
    try:
        participant = await ctx.wait_for_participant()
        user_id = (
            participant.identity
            if participant and participant.identity
            else "default_user"
        )
        user_data = get_or_create_user(user_id=user_id)
        session.userdata["user_id"] = user_id
        ctx.proc.userdata["user_id"] = user_id

        # Launch non-blocking background task to pre-fetch memory cache
        prefetch_task = asyncio.create_task(async_prefetch_user_memory(user_id))
        ctx.proc.userdata["prefetch_task"] = prefetch_task

        # Deliver automatic personalized greeting
        has_history = False
        if user_data:
            name = user_data.get("name")
            facts = user_data.get("facts") or {}
            goal = facts.get("learning_goal")
            topics = facts.get("topics_practiced") or []
            if name or (goal and goal != "everyday conversation") or topics:
                has_history = True

        if has_history:
            name = user_data.get("name")
            facts = user_data.get("facts") or {}
            goal = facts.get("learning_goal")
            topics = facts.get("topics_practiced") or []
            name_label = f"'{name}'" if name else "friend"
            goal_info = f" Saved goal: '{goal}'." if goal else ""
            topic_info = f" Previously practiced: '{topics[-1]}'." if topics else ""
            greeting_instruction = (
                f"This is a RETURNING USER. Preferred name: {name_label}.{goal_info}{topic_info} "
                f"Greet them enthusiastically in 1 short sentence starting with 'Welcome back {name or ''}!' as BolBuddy, mention you are glad to see them again, and ask what they want to practice today."
            )
        else:
            greeting_instruction = "Greet the user cheerfully in 1 short sentence as BolBuddy, ask for their preferred name so you can save it to memory, and ask what they want to practice today."

        # Deliver automatic initial greeting as a safe background task so LLM turn pipeline remains active
        async def _deliver_greeting():
            try:
                await session.generate_reply(instructions=greeting_instruction)
            except Exception as e:
                logger.warning(
                    f"Initial greeting generation exception (non-fatal): {e}"
                )

        greeting_task = asyncio.create_task(_deliver_greeting())
        ctx.proc.userdata["greeting_task"] = greeting_task
    except Exception as err:
        logger.warning(f"Participant greeting setup skipped: {err}")


if __name__ == "__main__":
    cli.run_app(server)
