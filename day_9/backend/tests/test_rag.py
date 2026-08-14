"""
Unit and evaluation test suite for HealthSathi RAG system (src/rag.py).
"""

import pytest
from livekit.agents import inference, llm

from rag import query_health_resources, search_health_resources


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.mark.asyncio
async def test_rag_symptom_question():
    """Test 1: Fever symptom question retrieves symptom_basics.md."""
    res = query_health_resources("What should I do if I have a fever?")
    assert res is not None
    assert "Symptom" in res["title"]


@pytest.mark.asyncio
async def test_rag_doctor_prep_question():
    """Test 2: Doctor visit question retrieves doctor_visit_prep.md."""
    res = query_health_resources(
        "What questions should I ask my doctor during a visit?"
    )
    assert res is not None
    assert "Doctor" in res["title"]


@pytest.mark.asyncio
async def test_rag_medication_safety_question():
    """Test 3: Medication question retrieves medication_safety.md."""
    res = query_health_resources("How do I take my medication safely and consistently?")
    assert res is not None
    assert "Medication" in res["title"]


@pytest.mark.asyncio
async def test_rag_urgent_care_question():
    """Test 4: Urgent warning signs question retrieves urgent_care_guidance.md."""
    res = query_health_resources(
        "What are the severe warning signs for immediate emergency care?"
    )
    assert res is not None
    assert "Urgent" in res["title"] or "Care" in res["title"]


@pytest.mark.asyncio
async def test_rag_hinglish_symptom_question():
    """Test 5: Hinglish health question retrieves relevant document snippet."""
    res = query_health_resources(
        "Mujhe doctor visit ke liye kya questions prepare karne chahiye?"
    )
    assert res is not None
    assert "Doctor" in res["title"]


@pytest.mark.asyncio
async def test_rag_irrelevant_question():
    """Test 6: Irrelevant query returns None and tool returns 'No relevant health guidance document found.'."""
    res = query_health_resources("How do I bake a chocolate cake recipe step by step?")
    assert res is None

    tool_res = await search_health_resources(
        context=None, query="How do I bake a chocolate cake recipe?"
    )
    assert "No relevant health guidance document found" in tool_res


@pytest.mark.asyncio
async def test_rag_no_relevant_document():
    """Test 7: Query outside health domain returns no relevant document without pretending."""
    tool_res = await search_health_resources(
        context=None,
        query="What is the quantum mechanics theory of black hole event horizons?",
    )
    assert "No relevant health guidance document found" in tool_res
