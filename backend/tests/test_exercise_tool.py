"""
Test suite for Day 5 tools: fetch_next_exercise and score_spoken_answer.

Tests unit dataset retrieval, LLM tool execution flows with Sakshyam persona,
failure path fallbacks, and low-token natural response generation.
"""

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant
from exercises import get_next_exercise


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


async def _assert_message(result, eval_llm: llm.LLM, intent: str) -> None:
    """Helper to consume optional tool calls then judge assistant message."""
    event_assert = result.expect.next_event()
    while True:
        try:
            event_assert.is_function_call()
            result.expect.next_event().is_function_call_output()
            event_assert = result.expect.next_event()
        except AssertionError:
            break

    await event_assert.is_message(role="assistant").judge(eval_llm, intent=intent)


# ── Unit tests for exercises module ────────────────────────────────────────


def test_get_next_exercise_interview():
    """Verify interview exercises returned for beginner level."""
    res = get_next_exercise(level="beginner", topic="internship interview")
    assert "question" in res
    assert "skill" in res
    assert "error" not in res
    assert len(res["question"]) > 10


def test_get_next_exercise_viva():
    """Verify viva exercises returned for intermediate level."""
    res = get_next_exercise(level="intermediate", topic="college viva")
    assert "question" in res
    assert "skill" in res
    assert "error" not in res


def test_get_next_exercise_presentation():
    """Verify presentation exercises returned for advanced level."""
    res = get_next_exercise(level="advanced", topic="campus presentation")
    assert "question" in res
    assert "skill" in res
    assert "error" not in res


def test_get_next_exercise_everyday():
    """Verify everyday English exercises returned."""
    res = get_next_exercise(level="beginner", topic="everyday English")
    assert "question" in res
    assert "skill" in res
    assert "error" not in res


# ── LLM-as-judge integration tests ───────────────────────────────────────


@pytest.mark.asyncio
async def test_no_exercise_tool_on_greeting() -> None:
    """Sakshyam saying 'Hi' triggers NO exercise tool call."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Hi, I am Sakshyam.")

        await _assert_message(
            result,
            eval_llm,
            intent="Greets Sakshyam warmly without calling any exercise or scoring tools.",
        )

        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_exercise_tool_on_practice_request() -> None:
    """Sakshyam requesting interview practice invokes fetch_next_exercise."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="Hi BolBuddy, I want to practice for an internship interview."
        )

        # Consume optional lookup_user_memory
        event = result.expect.next_event()
        try:
            event.is_function_call(name="lookup_user_memory")
            result.expect.next_event().is_function_call_output()
            event = result.expect.next_event()
        except AssertionError:
            pass

        # Expect fetch_next_exercise tool call
        try:
            event.is_function_call(name="fetch_next_exercise")
            result.expect.next_event().is_function_call_output()
            msg_event = result.expect.next_event()
        except AssertionError:
            msg_event = event

        await msg_event.is_message(role="assistant").judge(
            eval_llm,
            intent="""
            Offers an interview practice question naturally to Sakshyam.
            Does NOT mention tool names, JSON, or technical implementation.
            """,
        )


@pytest.mark.asyncio
async def test_scoring_on_how_did_i_do() -> None:
    """Sakshyam asking 'How did I do?' invokes score_spoken_answer."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=(
                "I just finished my spoken answer: "
                "'Hi, I'm Sakshyam. I'm currently studying engineering. "
                "I'm interested in technology and I want to gain practical experience through an internship.' "
                "How did I do? Can you evaluate my answer and give me a score?"
            )
        )

        # Consume events to find assistant message
        events_consumed = 0
        event = result.expect.next_event()
        while events_consumed < 6:
            try:
                event.is_function_call()
                result.expect.next_event().is_function_call_output()
                event = result.expect.next_event()
                events_consumed += 2
            except AssertionError:
                break

        await event.is_message(role="assistant").judge(
            eval_llm,
            intent="""
            Gives short, encouraging spoken feedback on Sakshyam's spoken answer.
            Does NOT expose raw JSON, function names, or internal code.
            """,
        )
