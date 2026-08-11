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
from exercises import (
    get_next_exercise as fn_get_next_exercise,
)
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
from scoring import (
    score_spoken_answer as fn_score_spoken_answer,
)

logger = logging.getLogger("agent")
load_dotenv(".env.local")


def _prune_history(session: AgentSession, max_turns: int = 4) -> None:
    """Keep system prompt + most recent max_turns messages to maintain low token usage and avoid TPM limits."""
    try:
        if (
            hasattr(session, "chat_ctx")
            and session.chat_ctx
            and hasattr(session.chat_ctx, "messages")
        ):
            msgs = session.chat_ctx.messages
            if len(msgs) > max_turns + 1:
                system_msg = (
                    [msgs[0]]
                    if (msgs and getattr(msgs[0], "role", None) == "system")
                    else []
                )
                recent_msgs = msgs[-max_turns:]
                session.chat_ctx.messages = system_msg + [
                    m for m in recent_msgs if m not in system_msg
                ]
                logger.info(
                    f"Pruned chat context history to {len(session.chat_ctx.messages)} messages for token optimization"
                )
    except Exception as e:
        logger.warning(f"Failed to prune chat context history: {e}")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

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
        logger.info(
            f"TOOL CALL: save_user_memory (name='{name}', goal='{learning_goal}')"
        )
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
        logger.info(f"TOOL COMPLETE: save_user_memory -> {res}")
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
        logger.info(f"TOOL COMPLETE: forget_my_data -> {res}")
        return res

    @function_tool
    async def what_do_you_remember(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Summarize saved user memory. Use only when user explicitly asks what is remembered."""
        logger.info(f"TOOL CALL: what_do_you_remember (user_id='{user_id}')")
        res = await fn_what_do_you_remember(context, user_id=user_id)
        logger.info("TOOL COMPLETE: what_do_you_remember")
        return res

    @function_tool
    async def search_learning_resources(
        self,
        context: RunContext,
        query: str = "",
    ) -> str:
        """Search learning resources for grammar rules, viva tips, or interview prep."""
        logger.info(f"TOOL CALL: search_learning_resources (query='{query}')")
        res = await fn_search_learning_resources(context, query=query)
        logger.info("TOOL COMPLETE: search_learning_resources")
        return res

    @function_tool
    async def fetch_next_exercise(
        self,
        context: RunContext,
        level: str = "beginner",
        topic: str = "interview",
    ) -> str:
        """Return one speaking exercise for requested level and topic. Use only when learner requests practice or a new exercise."""
        logger.info(
            f"TOOL CALL: fetch_next_exercise (level='{level}', topic='{topic}')"
        )
        res_dict = fn_get_next_exercise(level=level, topic=topic)
        import json

        res_str = json.dumps(res_dict)
        logger.info("TOOL COMPLETE: fetch_next_exercise")
        return res_str

    @function_tool
    async def score_spoken_answer(
        self,
        context: RunContext,
        question: str = "",
        answer: str = "",
        transcript: str = "",
        practice_topic: str = "",
    ) -> str:
        """Evaluate a completed spoken answer. Use only when learner explicitly asks for feedback, evaluation, or a score."""
        logger.info("TOOL CALL: score_spoken_answer")
        res = await fn_score_spoken_answer(
            context,
            question=question,
            answer=answer,
            transcript=transcript,
            practice_topic=practice_topic,
        )
        logger.info("TOOL COMPLETE: score_spoken_answer")
        return res

    @function_tool
    async def end_call(
        self,
        context: RunContext,
        reason: str = "DECLINED",
    ) -> str:
        """End the outbound call session cleanly after user declines or asks to disconnect."""
        logger.info(f"TOOL CALL: end_call (reason='{reason}')")
        try:
            sess = getattr(context, "session", None)
            if sess:
                room_io = getattr(sess, "room_io", None)
                if room_io and hasattr(room_io, "room") and room_io.room:

                    async def _disconnect_delay():
                        await asyncio.sleep(2.5)
                        try:
                            await room_io.room.disconnect()
                        except Exception as disc_err:
                            logger.warning(f"Disconnect error: {disc_err}")

                    disc_task = asyncio.create_task(_disconnect_delay())
                    if hasattr(sess, "userdata") and isinstance(sess.userdata, dict):
                        sess.userdata["disc_task"] = disc_task
        except Exception as e:
            logger.warning(f"Failed to schedule room disconnect: {e}")
        return f"Call ended gracefully ({reason})."


def _clean_tts_text(text: str) -> str:
    """Sanitize spoken text output to ensure no raw tool tags, XML, or JSON reach TTS audio synthesis."""
    if not text:
        return ""
    import re

    # Remove function/XML tags like <a function=...>, <function=...>, </function>, <tool_call>, etc.
    text = re.sub(r"<[^>]+>", "", text)
    # Remove raw JSON structures {"...": ...}
    text = re.sub(r"\{[\s\S]*?\}", "", text)
    # Remove leaked function tool names
    text = re.sub(
        r"\b(save_user_memory|lookup_user_memory|forget_my_data|what_do_you_remember|fetch_next_exercise|score_spoken_answer|search_learning_resources)\b",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", text).strip()


server = AgentServer(job_executor_type=JobExecutorType.THREAD)


def prewarm(proc: JobProcess):
    # Responsive noise-resilient VAD tuned to avoid stuck-in-listening states
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=0.2,
        prefix_padding_duration=0.2,
        activation_threshold=0.3,
    )
    init_db()

    # Start persistent background daily practice scheduler
    try:
        from scheduler import start_scheduler_loop

        sched_task = asyncio.create_task(start_scheduler_loop())
        proc.userdata["sched_task"] = sched_task
    except Exception as sched_err:
        logger.warning(f"Could not start background scheduler: {sched_err}")


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # LLM Initialization: NVIDIA API Primary Provider
    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
    nvidia_model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct").strip()
    nvidia_base_url = os.getenv(
        "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
    ).strip()

    if nvidia_key:
        logger.info("LLM Provider: NVIDIA API")
        logger.info(f"LLM Model: {nvidia_model}")
        logger.info(f"LLM Base URL: {nvidia_base_url}")
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
            logger.info("LLM Fallback Provider: Google Gemini (gemini-2.0-flash)")
            llm = google.LLM(model="gemini-2.0-flash")
        else:
            logger.error("NVIDIA_API_KEY is not set in environment variables.")
            raise ValueError("NVIDIA_API_KEY is required to initialize BolBuddy agent.")

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
        # Responsive endpointing delays (0.2s silence threshold, 0.8s max phrase window)
        "min_endpointing_delay": 0.2,
        "max_endpointing_delay": 0.8,
        # Non-preemptive generation to prevent speculative tool execution conflicts
        "preemptive_generation": False,
        "tts_text_transforms": tts_transforms,
    }

    session = AgentSession(**session_kwargs)

    # Attach event listener for history pruning and token diagnostic logging on user turn
    # pyrefly: ignore [bad-argument-type]
    @session.on("user_speech_committed")
    def _on_user_speech(msg):
        _prune_history(session, max_turns=4)
        logger.info("USER TURN START")
        logger.info("LLM GENERATION START")

    # pyrefly: ignore [bad-argument-type]
    @session.on("agent_speech_started")
    def _on_agent_speech_started(msg):
        logger.info("LLM GENERATION COMPLETE")
        logger.info("TTS START")

    # pyrefly: ignore [bad-argument-type]
    @session.on("agent_speech_stopped")
    def _on_agent_speech_stopped(msg):
        logger.info("TTS COMPLETE")

    # Attach event listener for TPM rate-limit exception handling
    @session.on("error")
    def _on_session_error(err):
        err_str = str(err).lower()
        if "429" in err_str or "tpm" in err_str or "rate limit" in err_str:
            logger.error(f"LLM API rate limit error detected: {err}")

            async def _speak_error():
                try:
                    await session.say(
                        "I'm a little busy right now. Give me a few seconds and try again.",
                        allow_interruptions=True,
                    )
                except Exception as say_err:
                    logger.warning(f"Error speaking rate limit message: {say_err}")

            err_task = asyncio.create_task(_speak_error())
            ctx.proc.userdata["err_task"] = err_task

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
        ctx.proc.userdata["user_id"] = user_id

        # Launch non-blocking background task to pre-fetch memory cache
        prefetch_task = asyncio.create_task(async_prefetch_user_memory(user_id))
        ctx.proc.userdata["prefetch_task"] = prefetch_task

        # Check if room or participant represents an outbound call session
        is_outbound = False
        if (
            ctx.room
            and ctx.room.name
            and ("outbound" in ctx.room.name.lower() or "sip" in ctx.room.name.lower())
        ):
            is_outbound = True
        if (
            participant
            and getattr(participant, "attributes", None)
            and participant.attributes.get("is_outbound") == "true"
        ):
            is_outbound = True

        name = user_data.get("name") if user_data else None
        facts = user_data.get("facts") if user_data else {}
        goal = facts.get("learning_goal") if facts else None

        if is_outbound:
            if name:
                greeting_text = f"Hi {name}, this is BolBuddy, your English practice companion. You scheduled your daily practice call for this time. If you'd rather not practice now, just say so and I'll end the call. Want to practice for a few minutes?"
            else:
                greeting_text = "Hi, this is BolBuddy, your English practice companion. You scheduled your daily practice call for this time. If you'd rather not practice now, just say so and I'll end the call. Want to practice for a few minutes?"
        elif name:
            greeting_text = f"Welcome back {name}! It's great to see you again. What would you like to practice today?"
        elif goal and goal != "everyday conversation":
            greeting_text = f"Hello! Ready to practice your {goal} today?"
        else:
            greeting_text = "Welcome! I'm BolBuddy, your English speaking companion. What's your name, and what would you like to practice today?"

        async def _deliver_greeting():
            try:
                await session.say(greeting_text, allow_interruptions=True)
            except Exception as e:
                logger.warning(f"Initial greeting delivery exception (non-fatal): {e}")

        greeting_task = asyncio.create_task(_deliver_greeting())
        ctx.proc.userdata["greeting_task"] = greeting_task
    except Exception as err:
        logger.warning(f"Participant greeting setup skipped: {err}")


if __name__ == "__main__":
    cli.run_app(server)
