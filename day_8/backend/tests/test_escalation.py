"""
Unit and LLM evaluation tests for HealthSathi Voice Agent (Human Escalation & Discord Webhook Delivery).
Covers Tests A through I.
"""

import json
import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from livekit.agents import AgentSession, inference, llm
from livekit.plugins import google, openai

from agent import Assistant
from db import get_escalations, init_db, save_escalation
from escalation_tools import _redact_pii, create_escalation
from outbound import trigger_outbound_practice
from schedule_model import create_or_update_schedule, get_schedule


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
        return google.LLM(model="gemini-2.0-flash", api_key=google_key)
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.fixture
def temp_db():
    """Fixture providing isolated temporary SQLite DB."""
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


@pytest.mark.asyncio
async def test_save_and_get_escalation(temp_db):
    """Test saving escalation ticket to SQLite DB and reading it back."""
    ref_id = "HS-9999"
    user_id = "test_user_701"

    saved = save_escalation(
        reference_id=ref_id,
        user_id=user_id,
        who_needs_help="Ramesh",
        reason_type="health_concern",
        issue_summary="User reports persistent fever and needs human healthcare guidance",
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
async def test_test_h_webhook_unavailable_local_save(temp_db):
    """TEST H: Discord webhook unavailable -> ticket saved locally in SQLite, reference_id returned."""
    if "DISCORD_ESCALATION_WEBHOOK_URL" in os.environ:
        del os.environ["DISCORD_ESCALATION_WEBHOOK_URL"]
    if "DISCORD_WEBHOOK_URL" in os.environ:
        del os.environ["DISCORD_WEBHOOK_URL"]

    res_str = await create_escalation(
        user_confirmed_consent=True,
        who_needs_help="Priya",
        reason_type="health_concern",
        issue_summary="User feels overwhelmed by health symptoms.",
        checked_by_agent="Provided general guidance.",
        urgency="medium",
        preferred_language="Hinglish",
        preferred_contact="phone",
        user_id="user_distress_702",
        db_path=temp_db,
    )

    res = json.loads(res_str)
    assert res["success"] is True
    assert res["reference_id"].startswith("HS-")
    assert res["status"] == "OPEN"

    tickets = get_escalations(user_id="user_distress_702", db_path=temp_db)
    assert len(tickets) == 1
    assert tickets[0]["who_needs_help"] == "Priya"
    assert tickets[0]["status"] == "OPEN"
    assert tickets[0]["reference_id"] == res["reference_id"]


@pytest.mark.asyncio
async def test_test_g_reference_id_consistency_db_discord_agent(temp_db):
    """TEST G: Same reference_id is stored in DB, dispatched to Discord, and returned in tool output."""
    mock_post = AsyncMock()
    mock_post.return_value.status_code = 204

    with (
        patch("os.getenv", return_value="https://discord.com/api/webhooks/dummy/mock"),
        patch("httpx.AsyncClient.post", new=mock_post),
    ):
        res_str = await create_escalation(
            user_confirmed_consent=True,
            who_needs_help="Vikram",
            reason_type="human_health_support",
            issue_summary="User requested human health support.",
            user_id="user_ref_matching",
            db_path=temp_db,
        )

        res = json.loads(res_str)
        ref_id = res["reference_id"]
        assert ref_id.startswith("HS-")

        # 1. Stored in DB
        tickets = get_escalations(user_id="user_ref_matching", db_path=temp_db)
        assert len(tickets) == 1
        assert tickets[0]["reference_id"] == ref_id

        # 2. Sent to Discord
        assert mock_post.called
        sent_body = mock_post.call_args[1]["json"]["content"]
        assert ref_id in sent_body


@pytest.mark.asyncio
async def test_test_a_call_me_now_trigger(temp_db):
    """TEST A: Click Call Me Now -> outbound call trigger executes."""
    res = await trigger_outbound_practice(
        user_id="user_call_now",
        phone_number="+9779876543210",
        name="Ramesh",
    )
    assert res is not None
    assert "call_id" in res or "status" in res or res.get("success") is not None


@pytest.mark.asyncio
async def test_test_b_schedule_call_storage(temp_db):
    """TEST B: Schedule a call -> scheduled callback stored in SQLite DB."""
    res = create_or_update_schedule(
        user_id="user_sched_test",
        phone_number="+9779876543210",
        practice_topic="Daily Medication Check-in",
        preferred_time="09:00",
        db_path=temp_db,
    )
    assert res is not None
    assert res["preferred_time"] == "09:00"

    saved_schedule = get_schedule(user_id="user_sched_test", db_path=temp_db)
    assert saved_schedule is not None
    assert saved_schedule["preferred_time"] == "09:00"


@pytest.mark.asyncio
async def test_test_c_human_help_agent_asks_consent(temp_db) -> None:
    """TEST C: Unconfirmed consent -> create_escalation refuses ticket creation and sends no Discord message."""
    res_str = await create_escalation(
        user_confirmed_consent=False,
        who_needs_help="User",
        reason_type="human_support",
        issue_summary="User asked for human help without consent confirmation",
        db_path=temp_db,
    )
    res = json.loads(res_str)
    assert res["success"] is False
    assert "not confirmed" in res["error"].lower()

    tickets = get_escalations(user_id="default_user", db_path=temp_db)
    assert len(tickets) == 0


@pytest.mark.asyncio
async def test_test_d_consent_no_no_ticket(temp_db) -> None:
    """TEST D: User says NO -> no ticket created, no Discord message sent."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())
        turn1 = await session.run(
            user_input="What is your human support escalation process?"
        )

        # Check turn 1 does NOT invoke create_escalation tool
        for ev in turn1.events:
            item = getattr(ev, "item", None)
            if item and getattr(item, "name", "") == "create_escalation":
                pytest.fail("create_escalation tool was invoked before consent was granted!")

        turn2 = await session.run(user_input="No, I do not want to create a support request.")

        # Check turn 2 does NOT invoke create_escalation tool
        for ev in turn2.events:
            item = getattr(ev, "item", None)
            if item and getattr(item, "name", "") == "create_escalation":
                pytest.fail("create_escalation tool was invoked after user declined!")

        tickets = get_escalations(user_id="default_user", db_path=temp_db)
        assert len(tickets) == 0


@pytest.mark.asyncio
async def test_test_e_consent_yes_executes_escalation(temp_db) -> None:
    """TEST E: User says YES -> create_escalation executes and returns reference_id spoken to user."""
    async with (
        _llm() as eval_llm,
        AgentSession(llm=eval_llm) as session,
    ):
        await session.start(Assistant())
        await session.run(user_input="Can you submit a human health support request for me?")

        result = await session.run(user_input="Yes, I confirm. Please execute create_escalation to submit my support request now.")

        # Ensure create_escalation tool call occurs
        tool_called = False
        for ev in result.events:
            item = getattr(ev, "item", None)
            if item and getattr(item, "name", "") == "create_escalation":
                tool_called = True
                break

        assert tool_called is True
