"""
Unit and LLM evaluation tests for BolBuddy Voice Agent Day 7 (Human Escalation & Discord Webhook Delivery).
"""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from livekit.agents import AgentSession, inference, llm
from livekit.plugins import google, openai

from agent import Assistant
from db import get_escalations, init_db, save_escalation
from escalation_tools import _redact_pii, create_escalation, send_escalation_webhook


def _llm() -> llm.LLM:
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if openrouter_key:
        return openai.LLM(
            model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct"),
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
    google_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if google_key:
        return google.LLM(model="gemini-2.5-flash", api_key=google_key)
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.fixture
def temp_db():
    """Fixture providing isolated temporary SQLite DB."""
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
async def test_save_and_get_escalation(temp_db):
    """Test saving escalation ticket to SQLite DB and reading it back."""
    ref_id = "ESC-9999"
    user_id = "test_user_701"

    saved = save_escalation(
        reference_id=ref_id,
        user_id=user_id,
        who_needs_help="Ramesh",
        reason_type="human_teacher_request",
        issue_summary="Needs 1-on-1 coaching for TOEFL speaking",
        urgency="high",
        preferred_language="Hindi",
        preferred_contact="phone",
        status="OPEN",
        db_path=temp_db,
    )

    assert saved is not None
    assert saved["reference_id"] == ref_id
    assert saved["status"] == "OPEN"

    all_tickets = get_escalations(user_id=user_id, db_path=temp_db)
    assert len(all_tickets) == 1
    assert all_tickets[0]["who_needs_help"] == "Ramesh"
    assert all_tickets[0]["urgency"] == "high"


@pytest.mark.asyncio
async def test_test_f_pii_redaction():
    """TEST F: PII included in input is removed before Discord notification."""
    raw_text = "User Ramesh said my password is MyPass123! and my OTP code is 849201. Account 4532 9981 1234 5678."
    redacted = _redact_pii(raw_text)

    assert "MyPass123!" not in redacted
    assert "849201" not in redacted
    assert "4532 9981 1234 5678" not in redacted
    assert "[REDACTED]" in redacted or "[ACCOUNT-REDACTED]" in redacted


@pytest.mark.asyncio
async def test_test_e_discord_webhook_unavailable(temp_db):
    """TEST E: Discord webhook unavailable -> SQLite escalation still created, agent continues normally, no crash."""
    # Ensure webhook URL env var is unset
    if "DISCORD_ESCALATION_WEBHOOK_URL" in os.environ:
        del os.environ["DISCORD_ESCALATION_WEBHOOK_URL"]
    if "DISCORD_WEBHOOK_URL" in os.environ:
        del os.environ["DISCORD_WEBHOOK_URL"]

    res = await create_escalation(
        who_needs_help="Priya",
        reason_type="learner_distress",
        issue_summary="Learner feels extremely anxious and overwhelmed about speaking in public.",
        checked_by_agent="Provided encouraging feedback.",
        urgency="medium",
        preferred_language="Hinglish",
        preferred_contact="email",
        user_id="user_distress_702",
        db_path=temp_db,
    )

    assert "ESC-" in res
    assert "Your support request has been created." in res

    # SQLite record must exist regardless of webhook availability
    tickets = get_escalations(user_id="user_distress_702", db_path=temp_db)
    assert len(tickets) == 1
    assert tickets[0]["who_needs_help"] == "Priya"
    assert tickets[0]["status"] == "OPEN"


@pytest.mark.asyncio
async def test_test_g_duplicate_open_escalation(temp_db):
    """TEST G: Duplicate open escalation updates existing record without creating duplicate ticket."""
    user_id = "user_dup_703"

    res1 = await create_escalation(
        who_needs_help="Vikram",
        reason_type="human_teacher_request",
        issue_summary="Wants human teacher to review viva answer.",
        user_id=user_id,
        db_path=temp_db,
    )
    assert "ESC-" in res1

    tickets_initial = get_escalations(user_id=user_id, db_path=temp_db)
    assert len(tickets_initial) == 1
    ref_id = tickets_initial[0]["reference_id"]

    res2 = await create_escalation(
        who_needs_help="Vikram",
        reason_type="human_teacher_request",
        issue_summary="Also needs help with grammar evaluation.",
        user_id=user_id,
        db_path=temp_db,
    )
    assert ref_id in res2

    tickets_after = get_escalations(user_id=user_id, db_path=temp_db)
    assert len(tickets_after) == 1
    assert (
        "Also needs help with grammar evaluation" in tickets_after[0]["issue_summary"]
    )


@pytest.mark.asyncio
async def test_test_c_webhook_success_dispatch(temp_db):
    """TEST C: Webhook success -> sends Discord notification and returns confirmation message."""
    mock_post = AsyncMock()
    mock_post.return_value.status_code = 204

    with (
        patch("os.getenv", return_value="https://discord.com/api/webhooks/dummy/mock"),
        patch("httpx.AsyncClient.post", new=mock_post),
    ):
        escalation_data = {
            "reference_id": "ESC-7777",
            "who_needs_help": "Ananya",
            "reason_type": "Human Teacher Request",
            "issue_summary": "Wants 1-on-1 coaching",
            "urgency": "medium",
            "preferred_language": "English",
            "preferred_contact": "phone",
            "status": "OPEN",
        }

        success = await send_escalation_webhook(escalation_data)
        assert success is True
        assert mock_post.called


@pytest.mark.asyncio
async def test_test_b_human_teacher_request_consent_required() -> None:
    """TEST B: Human teacher request -> consent requested, NO escalation before consent."""
    async with (
        _llm() as llm_obj,
        AgentSession(llm=llm_obj) as session,
    ):
        await session.start(Assistant())

        result1 = await session.run(
            user_input="I want to talk to a real English teacher. I need one-on-one help."
        )

        # Must NOT execute create_escalation tool on first turn
        for event in result1.events:
            if hasattr(event, "name"):
                assert event.name != "create_escalation"

        await (
            result1.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm_obj,
                intent="""
                Acknowledges request sympathetically.
                Asks explicit permission to send the request or share details with human support team.
                Does NOT execute create_escalation tool before receiving permission.
                """,
            )
        )


@pytest.mark.asyncio
async def test_test_a_normal_conversation_no_escalation() -> None:
    """TEST A: Normal conversation -> No escalation, No Discord notification."""
    async with (
        _llm() as llm_obj,
        AgentSession(llm=llm_obj) as session,
    ):
        await session.start(Assistant())

        result = await session.run(
            user_input="Hi! I want to practice introducing myself for a job interview."
        )

        for event in result.events:
            if hasattr(event, "name"):
                assert event.name != "create_escalation"


@pytest.mark.asyncio
async def test_test_d_consent_denied_no_escalation() -> None:
    """TEST D: Consent NO -> No escalation, No Discord webhook."""
    async with (
        _llm() as llm_obj,
        AgentSession(llm=llm_obj) as session,
    ):
        await session.start(Assistant())

        _ = await session.run(user_input="I want a real human teacher to help me.")

        result2 = await session.run(user_input="No, don't share my information.")

        for event in result2.events:
            if hasattr(event, "name"):
                assert event.name != "create_escalation"

        await (
            result2.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm_obj,
                intent="""
                Politely acknowledges user decision not to share information.
                Does NOT create a ticket or claim a request was sent.
                """,
            )
        )
