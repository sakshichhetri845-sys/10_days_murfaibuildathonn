"""
Multilingual and code-mixed memory unit and evaluation tests for BolBuddy (Phase 6).
"""

import os
import tempfile

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant
from db import get_user, init_db
from memory_tools import save_user_memory


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.fixture
def temp_db():
    """Fixture providing a temporary SQLite database file for isolated testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    init_db(db_path=db_path)
    os.environ["BOLBUDDY_DB_PATH"] = db_path
    yield db_path

    if "BOLBUDDY_DB_PATH" in os.environ:
        del os.environ["BOLBUDDY_DB_PATH"]

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        pass


@pytest.mark.asyncio
async def test_multilingual_english_memory_saving(temp_db):
    """Test 1: English utterance saves language-neutral memory facts."""
    user_id = "multi_en_user_101"

    # User utterance: "I want to practice interview English."
    res = await save_user_memory(
        context=None,
        name="John",
        language_preference="English",
        learning_goal="job interview",
        topic_practiced="interview English",
        user_id=user_id,
    )
    assert res == "Memory saved successfully."

    saved = get_user(user_id=user_id, db_path=temp_db)
    assert saved["facts"]["learning_goal"] == "job interview"
    assert "interview English" in saved["facts"]["topics_practiced"]
    # Ensure raw sentence is NOT stored as primary memory
    assert "I want to practice interview English." not in saved["facts"]


@pytest.mark.asyncio
async def test_multilingual_hindi_memory_saving(temp_db):
    """Test 2: Hindi utterance saves language-neutral memory facts."""
    user_id = "multi_hi_user_102"

    # User utterance: "मुझे इंटरव्यू के लिए अंग्रेज़ी की प्रैक्टिस करनी है।"
    res = await save_user_memory(
        context=None,
        name="रमेश",
        language_preference="Hindi",
        learning_goal="job interview",
        topic_practiced="self introduction",
        user_id=user_id,
    )
    assert res == "Memory saved successfully."

    saved = get_user(user_id=user_id, db_path=temp_db)
    assert saved["facts"]["learning_goal"] == "job interview"
    # Verify non-raw language-neutral storage
    assert "मुझे इंटरव्यू के लिए अंग्रेज़ी की प्रैक्टिस करनी है।" not in saved["facts"]


@pytest.mark.asyncio
async def test_multilingual_hinglish_memory_saving(temp_db):
    """Test 3: Hinglish utterance saves language-neutral memory facts."""
    user_id = "multi_hinglish_user_103"

    # User utterance: "Mujhe interview ke liye English practice karni hai."
    res = await save_user_memory(
        context=None,
        name="Sakshyam",
        language_preference="Hinglish",
        learning_goal="job interview",
        topic_practiced="interview questions",
        user_id=user_id,
    )
    assert res == "Memory saved successfully."

    saved = get_user(user_id=user_id, db_path=temp_db)
    assert saved["language_preference"] == "Hinglish"
    assert saved["facts"]["learning_goal"] == "job interview"


@pytest.mark.asyncio
async def test_multilingual_code_mixed_challenge_saving(temp_db):
    """Test 4: Mixed utterance extracts language-neutral goal and qualitative challenge tag."""
    user_id = "multi_mixed_user_104"

    # User utterance: "Actually mujhe English mein answer dena hai but I get nervous."
    res = await save_user_memory(
        context=None,
        language_preference="English + Hindi",
        learning_goal="job interview",
        recurring_challenge="nervousness",
        user_id=user_id,
    )
    assert res == "Memory saved successfully."

    saved = get_user(user_id=user_id, db_path=temp_db)
    assert saved["facts"]["learning_goal"] == "job interview"
    assert "nervousness" in saved["facts"]["recurring_challenges"]
    # Ensure raw utterance is not stored as raw key
    assert (
        "Actually mujhe English mein answer dena hai but I get nervous."
        not in saved["facts"]
    )


@pytest.mark.asyncio
async def test_returning_user_greeting_english(temp_db) -> None:
    """Evaluation of returning user greeting in English register."""
    user_id = "greet_en_user_201"
    await save_user_memory(
        context=None,
        name="Sakshyam",
        learning_goal="internship interview",
        user_id=user_id,
    )

    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=f"Hello BolBuddy! I am back. (User ID: {user_id})"
        )

        result.expect.next_event().is_function_call(name="lookup_user_memory")
        result.expect.next_event().is_function_call_output()

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                eval_llm,
                intent="""
                Welcomes Sakshyam back in warm conversational English.
                Refers to his internship interview preparation goal.
                Offers a helpful next step (e.g. practicing interview questions or self-introduction).
                """,
            )
        )

        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_returning_user_greeting_hindi(temp_db) -> None:
    """Evaluation of returning user greeting in Hindi register."""
    user_id = "greet_hi_user_202"
    await save_user_memory(
        context=None,
        name="Sakshyam",
        language_preference="Hindi",
        learning_goal="job interview",
        user_id=user_id,
    )

    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=f"नमस्ते बोलबडी, मैं वापस आ गया हूँ। (User ID: {user_id})"
        )

        result.expect.next_event().is_function_call(name="lookup_user_memory")
        result.expect.next_event().is_function_call_output()

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                eval_llm,
                intent="""
                Welcomes Sakshyam back in warm, encouraging Hindi or Hinglish mirroring the user's Hindi greeting.
                Acknowledges his interview practice goal and offers to practice together.
                """,
            )
        )

        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_returning_user_greeting_hinglish(temp_db) -> None:
    """Evaluation of returning user greeting in Hinglish register."""
    user_id = "greet_hinglish_user_203"
    await save_user_memory(
        context=None,
        name="Sakshyam",
        language_preference="Hinglish",
        learning_goal="viva",
        user_id=user_id,
    )

    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=f"Hey BolBuddy! Main wapas aa gaya. (User ID: {user_id})"
        )

        result.expect.next_event().is_function_call(name="lookup_user_memory")
        result.expect.next_event().is_function_call_output()

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                eval_llm,
                intent="""
                Welcomes Sakshyam back naturally in warm Hinglish/English.
                Refers to his viva / college project goal and offers helpful practice.
                """,
            )
        )

        result.expect.no_more_events()
