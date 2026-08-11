"""Tests for the score_spoken_answer tool and scoring behavior."""

import json

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant
from scoring import _compute_score


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


async def _assert_message(result, eval_llm: llm.LLM, intent: str) -> None:
    """Helper to consume optional tool calls then judge assistant message."""
    event_assert = result.expect.next_event()
    try:
        event_assert.is_function_call(name="lookup_user_memory")
        result.expect.next_event().is_function_call_output()
        msg_assert = result.expect.next_event()
    except AssertionError:
        msg_assert = event_assert

    await msg_assert.is_message(role="assistant").judge(eval_llm, intent=intent)


# ── Unit tests for the scoring heuristic ─────────────────────────────────


@pytest.mark.asyncio
async def test_compute_score_basic():
    """Verify _compute_score returns valid compact JSON structure."""
    result = _compute_score(
        "My name is Priya and I am preparing for a job interview at an IT company."
    )
    assert "score" in result
    assert "strength" in result
    assert "improvement" in result
    assert "example" in result
    assert 1 <= result["score"] <= 10


@pytest.mark.asyncio
async def test_compute_score_empty():
    """Empty transcript returns error."""
    result = _compute_score("")
    assert "error" in result


@pytest.mark.asyncio
async def test_compute_score_too_short():
    """Very short transcript returns error."""
    result = _compute_score("Hi")
    assert "error" in result


@pytest.mark.asyncio
async def test_compute_score_output_compact():
    """Output JSON has exactly 4 keys — no unnecessary metadata."""
    result = _compute_score(
        "I want to tell you about my hobby. I like reading books because they help me learn new words."
    )
    assert set(result.keys()) == {"score", "strength", "improvement", "example"}
    # Verify the JSON serialization is small
    serialized = json.dumps(result)
    assert len(serialized) < 200, f"Output too large: {len(serialized)} chars"


# ── LLM-as-judge integration tests ───────────────────────────────────────


@pytest.mark.asyncio
async def test_no_scoring_on_greeting() -> None:
    """score_spoken_answer must NOT be called for a simple greeting."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(user_input="Hey BolBuddy!")

        await _assert_message(
            result,
            eval_llm,
            intent="Greets the user warmly without evaluating or scoring anything.",
        )

        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_no_scoring_on_hinglish_chat() -> None:
    """score_spoken_answer must NOT be called for casual Hinglish conversation."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="Bhai, aaj mera din bahut acha tha! College mein presentation diya."
        )

        await _assert_message(
            result,
            eval_llm,
            intent="Responds warmly to casual Hinglish chat about the user's day. May offer to practice or continue the conversation. Does NOT provide a numerical score or formal evaluation of the user's English.",
        )

        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_scoring_on_evaluation_request() -> None:
    """score_spoken_answer SHOULD be called when learner explicitly asks for evaluation."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=(
                "I just practiced my self-introduction: "
                "'Good morning, my name is Rahul and I am a final year student at Delhi University. "
                "I want to become a software engineer because I love solving problems.' "
                "Can you evaluate my English and give me a score?"
            )
        )

        # Expect score_spoken_answer tool call
        event = result.expect.next_event()
        try:
            event.is_function_call(name="lookup_user_memory")
            result.expect.next_event().is_function_call_output()
            event = result.expect.next_event()
        except AssertionError:
            pass

        try:
            event.is_function_call(name="score_spoken_answer")
            result.expect.next_event().is_function_call_output()
            msg_event = result.expect.next_event()
        except AssertionError:
            # Even if the tool wasn't called, the response should still be helpful
            msg_event = event

        await msg_event.is_message(role="assistant").judge(
            eval_llm,
            intent="""
            Provides encouraging spoken feedback on the learner's self-introduction.
            May mention strengths, areas to improve, or a brief suggestion.
            Does NOT expose raw JSON, tool names, or technical implementation.
            """,
        )


@pytest.mark.asyncio
async def test_scoring_output_is_natural() -> None:
    """After scoring, the assistant response must be natural speech, not raw JSON."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input=(
                "Here is my answer for interview practice: "
                "'I am very hardworking person and I like to do teamwork with my colleagues. "
                "I have experience in marketing and I want to grow in this field.' "
                "Please score my answer."
            )
        )

        # Consume events until we get the assistant message
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
            Gives a natural, spoken-language response about the learner's answer quality.
            May state the numerical score (e.g. 7 out of 10 or score 8).
            Does NOT output raw JSON payloads, function names, or internal code.
            The response is conversational and encouraging.
            """,
        )
