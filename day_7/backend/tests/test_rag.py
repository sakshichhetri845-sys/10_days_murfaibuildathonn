"""
Unit and evaluation test suite for Lightweight RAG system (src/rag.py).
"""

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant
from rag import query_learning_resources, search_learning_resources


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.mark.asyncio
async def test_rag_grammar_question():
    """Test 1: Grammar question retrieves beginner_grammar.md."""
    res = query_learning_resources(
        "Is it correct to say myself Ramesh or my name is Ramesh?"
    )
    assert res is not None
    assert "Beginner Grammar" in res["title"]
    assert "Myself Ramesh" in res["content"] or "My name is" in res["content"]


@pytest.mark.asyncio
async def test_rag_interview_question():
    """Test 2: Interview question retrieves interview_english.md."""
    res = query_learning_resources(
        "How should I introduce myself in a job interview using STAR method?"
    )
    assert res is not None
    assert "Interview" in res["title"]


@pytest.mark.asyncio
async def test_rag_viva_question():
    """Test 3: Viva question retrieves viva_english.md."""
    res = query_learning_resources(
        "How to explain my project to professors during college viva defense?"
    )
    assert res is not None
    assert "Viva" in res["title"]


@pytest.mark.asyncio
async def test_rag_pronunciation_question():
    """Test 4: Pronunciation question retrieves pronunciation_tips.md."""
    res = query_learning_resources(
        "How do I distinguish V and W sounds in English pronunciation?"
    )
    assert res is not None
    assert "Pronunciation" in res["title"]


@pytest.mark.asyncio
async def test_rag_hinglish_question():
    """Test 5: Hinglish question retrieves relevant document snippet."""
    res = query_learning_resources(
        "Mujhe college presentation mein teammates ko hand over kaise karna hai?"
    )
    assert res is not None
    assert "College" in res["title"] or "Presentation" in res["title"]


@pytest.mark.asyncio
async def test_rag_irrelevant_question():
    """Test 6: Irrelevant query returns None and tool returns 'No relevant learning resource found.'."""
    res = query_learning_resources(
        "How do I bake a chocolate cake recipe step by step?"
    )
    assert res is None

    tool_res = await search_learning_resources(
        context=None, query="How do I bake a chocolate cake recipe?"
    )
    assert tool_res == "No relevant learning resource found."


@pytest.mark.asyncio
async def test_rag_no_relevant_document():
    """Test 7: Query outside learning domain returns 'No relevant learning resource found.' without pretending."""
    tool_res = await search_learning_resources(
        context=None,
        query="What is the quantum mechanics theory of black hole event horizons?",
    )
    assert tool_res == "No relevant learning resource found."


@pytest.mark.asyncio
async def test_rag_agent_spoken_voice_response_evaluation() -> None:
    """LLM-as-judge evaluation: Agent uses RAG knowledge in natural spoken voice without technical citations or verbatim reading."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="How can I pronounce V and W sounds clearly without getting confused?"
        )

        event_assert = result.expect.next_event()
        try:
            event_assert.is_function_call(name="search_learning_resources")
            result.expect.next_event().is_function_call_output()
            msg_assert = result.expect.next_event()
        except AssertionError:
            msg_assert = event_assert

        await msg_assert.is_message(role="assistant").judge(
            eval_llm,
            intent="""
            Explains how to pronounce V vs W clearly in a warm, encouraging, conversational voice.
            Does NOT say 'According to the knowledge base', 'In the document', or cite file names.
            Does NOT read markdown formatting verbatim.
            Keeps the explanation short and practical.
            """,
        )

        result.expect.no_more_events()
