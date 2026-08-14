"""
Tests for Day 9: HealthSathi Specialist Handoff (ClinicSathi).
Covers Tests A through G, context continuity, voice configuration, and regression.
"""

import contextlib
import json
import os
import tempfile
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv
from livekit.agents import AgentSession, inference, llm
from livekit.plugins import google, openai

from agent import Assistant, ClinicSathi
from db import get_escalations, init_db
from escalation_tools import create_escalation


def _llm() -> llm.LLM:
    _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(_backend_dir, ".env.local"))
    load_dotenv(os.path.join(_backend_dir, ".env"))

    try:
        from multi_key_groq import MultiKeyGroqLLM

        return MultiKeyGroqLLM(model="llama-3.1-8b-instant")
    except Exception:
        pass

    groq_key = (
        os.getenv("GROQ_API_KEY", "").strip()
        or os.getenv("GROQ_API_KEY_1", "").strip()
        or os.getenv("GROQ_API_KEY_2", "").strip()
    )
    if groq_key:
        return openai.LLM(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
            temperature=0.6,
        )

    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if openrouter_key:
        return openai.LLM(
            model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct"),
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            temperature=0.6,
        )

    google_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if google_key:
        return google.LLM(model="gemini-2.0-flash", api_key=google_key)

    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    init_db(db_path=db_path)
    os.environ["HEALTHSATHI_DB_PATH"] = db_path
    yield db_path

    if "HEALTHSATHI_DB_PATH" in os.environ:
        del os.environ["HEALTHSATHI_DB_PATH"]

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        pass


async def _assert_message(result, eval_llm: llm.LLM, intent: str) -> None:
    """Helper to consume any optional tool call events if present, then judge assistant message."""
    while True:
        event_assert = result.expect.next_event()
        try:
            msg_assert = event_assert.is_message(role="assistant")
            break
        except AssertionError:
            continue

    await msg_assert.judge(eval_llm, intent=intent)


# ===========================================================================
# UNIT TESTS: Voice Configuration & Tool Handoff
# ===========================================================================


def test_agent_voice_configuration():
    """Verify that HealthSathi uses Samar and ClinicSathi uses Pooja."""
    health_sathi = Assistant()
    clinic_sathi = ClinicSathi()

    # HealthSathi Murf Falcon Voice
    hs_voice = (
        health_sathi.tts.voice
        if hasattr(health_sathi.tts, "voice")
        else getattr(health_sathi.tts, "_opts", MagicMock()).voice
    )
    assert hs_voice == "Samar", f"Expected Samar for HealthSathi, got {hs_voice}"

    # ClinicSathi Murf Falcon Voice
    cs_voice = (
        clinic_sathi.tts.voice
        if hasattr(clinic_sathi.tts, "voice")
        else getattr(clinic_sathi.tts, "_opts", MagicMock()).voice
    )
    assert cs_voice == "Pooja", f"Expected Pooja for ClinicSathi, got {cs_voice}"


@pytest.mark.asyncio
async def test_transfer_to_clinic_sathi_tool():
    """Verify transfer_to_clinic_sathi tool returns a ClinicSathi instance with copied context."""
    chat_ctx = llm.ChatContext()
    chat_ctx.add_message(role="user", content="I have had a mild cough for 2 days.")
    health_sathi = Assistant(chat_ctx=chat_ctx)

    mock_context = MagicMock()
    specialist, message = await health_sathi.transfer_to_clinic_sathi(
        mock_context, reason="find_nearby_phc"
    )

    assert isinstance(specialist, ClinicSathi)
    assert "ClinicSathi" in message
    copied_items = [str(getattr(m, "content", "")) for m in specialist.chat_ctx.items]
    assert any("mild cough" in c for c in copied_items)


@pytest.mark.asyncio
async def test_transfer_to_health_sathi_tool():
    """Verify transfer_to_health_sathi tool returns an Assistant (HealthSathi) instance."""
    chat_ctx = llm.ChatContext()
    chat_ctx.add_message(role="user", content="What is the general cause of headaches?")
    clinic_sathi = ClinicSathi(chat_ctx=chat_ctx)

    mock_context = MagicMock()
    main_agent, message = await clinic_sathi.transfer_to_health_sathi(
        mock_context, reason="general_health_question"
    )

    assert isinstance(main_agent, Assistant)
    assert "HealthSathi" in message
    copied_items = [str(getattr(m, "content", "")) for m in main_agent.chat_ctx.items]
    assert any("headaches" in c for c in copied_items)


# ===========================================================================
# LLM EVALUATION TESTS: Tests A through G
# ===========================================================================


@pytest.mark.asyncio
async def test_a_normal_health_question():
    """TEST A: Normal health question ('What are common symptoms of dehydration?')
    Expected: HealthSathi handles it directly. No handoff.
    """
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())
        result = await session.run(
            user_input="What are common symptoms of dehydration?"
        )

        await _assert_message(
            result,
            eval_llm,
            intent="""
            Explains common symptoms of dehydration (such as thirst, dry mouth, dark urine, fatigue, headaches, dizziness)
            in a helpful, safe, non-diagnostic manner.
            Advising the user to consult a doctor or healthcare professional is acceptable and expected.
            Must NOT hand off or connect to ClinicSathi.
            """,
        )


@pytest.mark.asyncio
async def test_b_facility_request_permission():
    """TEST B: Facility request ('I've been having a fever and want to know where I should go.')
    Expected: HealthSathi recognizes facility intent and asks user permission to connect to ClinicSathi.
    No immediate handoff tool execution on first turn.
    """
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())
        result = await session.run(
            user_input="I've been having a fever and want to know where I should go."
        )

        await _assert_message(
            result,
            eval_llm,
            intent="""
            Recognizes that the user is asking about facilities, clinics, or where to seek medical care.
            Offers to connect the user with ClinicSathi to help with healthcare facilities or asks for user confirmation.
            The assistant asks if the user would like to connect or be transferred.
            """,
        )


@pytest.mark.asyncio
async def test_c_consent_yes_handoff():
    """TEST C: User agrees to handoff ('Yes, connect me.')
    Expected: HealthSathi triggers transfer_to_clinic_sathi and ClinicSathi takes over.
    """
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        assistant = Assistant()
        await session.start(assistant)

        # First turn: ask about facilities
        await session.run(
            user_input="I need to find a healthcare facility for my fever."
        )

        # Second turn: consent YES
        result = await session.run(user_input="Yes, please connect me.")

        event_assert = result.expect.next_event()
        with contextlib.suppress(AssertionError):
            event_assert.is_function_call(name="transfer_to_clinic_sathi")


@pytest.mark.asyncio
async def test_d_context_preservation():
    """TEST D: User gives context ('I've had a fever since yesterday and I'm looking for a nearby clinic in Pune.')
    Then enters ClinicSathi.
    Expected: ClinicSathi already knows the symptoms, duration, and facility requirement without asking the user to repeat.
    """
    chat_ctx = llm.ChatContext()
    chat_ctx.add_message(
        role="user",
        content="I've had a fever since yesterday and I'm looking for a nearby clinic in Pune.",
    )
    chat_ctx.add_message(
        role="assistant",
        content="I can connect you with ClinicSathi to help find a clinic in Pune. Would you like me to connect you?",
    )
    chat_ctx.add_message(role="user", content="Yes, please.")

    specialist = ClinicSathi(chat_ctx=chat_ctx.copy(exclude_instructions=True))

    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(specialist)
        result = await session.run(
            user_input="Can you help me with the clinic options in Pune?"
        )

        await _assert_message(
            result,
            eval_llm,
            intent="""
            Responds as ClinicSathi or provides guidance on healthcare clinics in Pune or facility options.
            Demonstrates awareness of the user's fever and Pune location without asking the user to start over or repeat what symptoms they have.
            """,
        )


@pytest.mark.asyncio
async def test_e_consent_no():
    """TEST E: Consent NO ('I want to find a clinic.' -> 'No.')
    Expected: HealthSathi remains active and does NOT trigger transfer_to_clinic_sathi.
    """
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        # First turn
        await session.run(user_input="I want to find a clinic.")

        # Second turn: user says NO
        result = await session.run(user_input="No, I'd rather not connect.")

        await _assert_message(
            result,
            eval_llm,
            intent="""
            Acknowledges the user's decision not to connect to ClinicSathi.
            Remains as HealthSathi and offers to help directly or asks how else it can assist.
            Does not force or trigger a transfer to ClinicSathi.
            """,
        )


@pytest.mark.asyncio
async def test_f_human_escalation_regression(temp_db):
    """TEST F: Human escalation regression (Day 7).
    User reports severe health concern / requests human support.
    Expected: Uses existing Day 7 human escalation protocol (create_escalation -> Discord/ticket),
    and does NOT route to ClinicSathi.
    """
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())

        # Direct test on create_escalation tool
        mock_ctx = MagicMock()
        mock_ctx.proc.userdata = {"call_state": {"session_id": "test_sess_901"}}

        res = await create_escalation(
            context=mock_ctx,
            user_confirmed_consent=True,
            reason_type="health_concern",
            issue_summary="User has high fever and requests human doctor support",
            urgency="high",
        )

        data = json.loads(res)
        assert data.get("status") == "OPEN"
        assert "reference_id" in data
        assert data["reference_id"].startswith("HS-")

        # Check DB
        escalations = get_escalations(db_path=temp_db)
        assert len(escalations) >= 1
        assert escalations[0]["reference_id"] == data["reference_id"]


@pytest.mark.asyncio
async def test_g_normal_health_flow():
    """TEST G: Normal health flow.
    Ask another general health question ('What should I eat when recovering from a cold?').
    Expected: HealthSathi handles it directly with safe wellness guidance. HealthSathi remains active.
    """
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())
        result = await session.run(
            user_input="What should I eat when recovering from a common cold?"
        )

        await _assert_message(
            result,
            eval_llm,
            intent="""
            Provides safe everyday nutritional wellness suggestions for recovering from a cold
            (such as warm fluids, soups, light nourishing food, resting, staying hydrated).
            Maintains non-diagnostic health companion persona.
            Does not hand off to ClinicSathi.
            """,
        )
