"""
Escalation tools module for HealthSathi Voice Agent.

Provides human escalation request creation, PII redaction, reference ID generation,
duplicate request prevention, SQLite persistence, and real Discord webhook dispatch.
"""

import json
import logging
import os
import random
import re
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

from db import get_open_escalation_by_user, save_escalation

logger = logging.getLogger("agent.escalation")
load_dotenv(".env.local")


def _redact_pii(text: str) -> str:
    """
    Sanitize and redact sensitive private information from summaries.
    Redacts OTPs, passwords, PINs, credit card / bank account numbers, and API tokens.
    """
    if not text:
        return ""

    sanitized = text

    # 1. Redact key-value or 'is' assignments for passwords, PINs, secret tokens
    sanitized = re.sub(
        r"\b(password|passcode|pwd|pin|otp|cvv|secret|token)\s*(?:is|[:=])\s*\S+",
        r"\1: [REDACTED]",
        sanitized,
        flags=re.IGNORECASE,
    )

    # 2. Redact 4 to 6 digit OTP / PIN codes
    sanitized = re.sub(
        r"\b(otp|pin|code)\s*(?:is|code)?\s*(\d{4,6})\b",
        r"\1: [REDACTED]",
        sanitized,
        flags=re.IGNORECASE,
    )

    # 3. Redact 12-16 digit bank / account / card numbers
    sanitized = re.sub(
        r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{2,4}\b",
        "[ACCOUNT-REDACTED]",
        sanitized,
    )

    return sanitized


def _generate_ref_id() -> str:
    """Generate a unique reference ID for escalation tracking (e.g., HS-4821)."""
    num = random.randint(1000, 9999)
    return f"HS-{num}"


def _get_webhook_url() -> Optional[str]:
    """Retrieve configured Discord escalation webhook URL from environment variables."""
    load_dotenv(".env.local")
    url = (
        os.getenv("DISCORD_ESCALATION_WEBHOOK_URL", "").strip()
        or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
        or os.getenv("ESCALATION_WEBHOOK_URL", "").strip()
    )
    if not url or "your_" in url.lower() or "example.com" in url.lower():
        return None
    return url


async def send_escalation_webhook(
    escalation: dict[str, Any], is_update: bool = False
) -> bool:
    """
    Send concise formatted escalation notification to Discord webhook channel.

    Returns True if Discord webhook POST succeeded (200/204), False otherwise.
    Never throws an exception or breaks the voice session.
    """
    webhook_url = _get_webhook_url()
    if not webhook_url:
        logger.info(
            "DISCORD_ESCALATION_WEBHOOK_URL is not configured; skipping Discord notification (SQLite escalation created)."
        )
        return False

    clean_summary = _redact_pii(escalation.get("issue_summary", ""))
    clean_checked = _redact_pii(
        escalation.get(
            "checked_by_agent",
            "Health guidance and general information provided prior to escalation request.",
        )
    )

    header_title = (
        f"🚨 **HealthSathi Human Support Request Updated: `{escalation['reference_id']}`**"
        if is_update
        else "🚨 **New HealthSathi Human Support Request**"
    )

    content_text = (
        f"{header_title}\n\n"
        f"**Reference:** {escalation.get('reference_id', 'N/A')}\n"
        f"**Reason:** {escalation.get('reason_type', 'Health Support')}\n"
        f"**Urgency:** {escalation.get('urgency', 'medium').capitalize()}\n\n"
        f"**User:**\n{escalation.get('who_needs_help', 'User')}\n\n"
        f"**Summary:**\n{clean_summary or 'User requested human health support.'}\n\n"
        f"**Language:** {escalation.get('preferred_language', 'English')}\n"
        f"**Follow-up:** {escalation.get('preferred_contact', 'phone')}\n\n"
        f"**Status:** {escalation.get('status', 'OPEN')}"
    )

    payload = {
        "content": content_text,
        "embeds": [
            {
                "title": f"HealthSathi Support Request ({escalation.get('urgency', 'medium').upper()})",
                "color": 15158332
                if escalation.get("urgency", "").lower() in ("high", "emergency")
                else 3447003,
                "fields": [
                    {
                        "name": "Reference ID",
                        "value": escalation.get("reference_id", "N/A"),
                        "inline": True,
                    },
                    {
                        "name": "Reason",
                        "value": escalation.get("reason_type", "Health Support"),
                        "inline": True,
                    },
                    {
                        "name": "Urgency",
                        "value": escalation.get("urgency", "medium").capitalize(),
                        "inline": True,
                    },
                    {
                        "name": "Language",
                        "value": escalation.get("preferred_language", "English"),
                        "inline": True,
                    },
                    {
                        "name": "User",
                        "value": escalation.get("who_needs_help", "User"),
                        "inline": True,
                    },
                    {
                        "name": "Preferred Follow-up",
                        "value": escalation.get("preferred_contact", "phone"),
                        "inline": True,
                    },
                    {
                        "name": "Summary",
                        "value": clean_summary or "No summary provided.",
                        "inline": False,
                    },
                    {
                        "name": "What HealthSathi Already Checked",
                        "value": clean_checked or "Health guidance provided.",
                        "inline": False,
                    },
                    {
                        "name": "Status",
                        "value": escalation.get("status", "OPEN"),
                        "inline": True,
                    },
                ],
                "footer": {"text": "HealthSathi Voice Companion — Human Support"},
            }
        ],
    }

    headers = {
        "User-Agent": "HealthSathi-VoiceAgent/1.0",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            res = await client.post(webhook_url, json=payload)
            if res.status_code in (200, 204):
                logger.info(
                    f"Successfully sent Discord webhook notification for {escalation['reference_id']}"
                )
                return True
            else:
                logger.warning(
                    f"Discord webhook dispatch returned HTTP {res.status_code}: {res.text}"
                )
                return False
    except Exception as e:
        logger.warning(f"Failed to dispatch Discord webhook: {e}")
        return False


def _check_user_explicit_consent(context: Any) -> bool:
    """Verify if the last user message in session context contains an explicit consent confirmation keyword."""
    if not context:
        return True

    sess = getattr(context, "session", None)
    if not sess:
        return True

    chat_ctx = getattr(sess, "chat_ctx", None)
    if not chat_ctx or not hasattr(chat_ctx, "messages"):
        return True

    user_msgs = [m for m in chat_ctx.messages if getattr(m, "role", "") == "user"]
    if not user_msgs:
        return True

    last_user_text = str(getattr(user_msgs[-1], "content", "") or "").lower()

    consent_keywords = [
        "yes", "yeah", "yep", "sure", "go ahead", "confirm", "submit",
        "please do", "share my data", "create ticket", "create a ticket",
        "i agree", "ok", "okay", "haan", "ha", "thik h", "thik hai", "call me", "connect me"
    ]

    return any(kw in last_user_text for kw in consent_keywords)


async def create_escalation(
    context: Any = None,
    user_confirmed_consent: bool = False,
    who_needs_help: str = "",
    reason_type: str = "health_concern",
    issue_summary: str = "",
    checked_by_agent: str = "",
    urgency: str = "medium",
    preferred_language: str = "English",
    preferred_contact: str = "phone",
    user_id: str = "",
    db_path: Optional[str] = None,
) -> str:
    """
    Core implementation of the human escalation tool for HealthSathi.

    1. Validates explicit user consent confirmation.
    2. Redacts PII from issue summary.
    3. Checks for existing open duplicate ticket.
    4. Creates/updates SQLite database record (Source of truth).
    5. Attempts Discord webhook notification.
    6. Returns clear status & reference ID to HealthSathi.
    """
    if not user_confirmed_consent or not _check_user_explicit_consent(context):
        logger.warning(
            "create_escalation invoked without explicit user consent in recent chat history. Ticket creation refused."
        )
        return json.dumps({
            "success": False,
            "error": "User consent is not confirmed. You MUST ask the user: 'Would you like me to create a support request and share a summary with our human support team?' and ONLY call this tool after the user explicitly says YES.",
        }, ensure_ascii=False)

    from db import init_db

    init_db(db_path=db_path)

    if not user_id and context:
        sess = getattr(context, "session", None)
        if sess:
            try:
                udata = getattr(sess, "userdata", None)
                if isinstance(udata, dict):
                    user_id = udata.get("user_id", "")
            except (ValueError, AttributeError):
                pass
    if not user_id:
        user_id = "default_user"

    if not who_needs_help:
        who_needs_help = f"User ({user_id})"

    clean_summary = _redact_pii(issue_summary)
    clean_checked = _redact_pii(checked_by_agent)

    valid_urgencies = ("low", "medium", "high", "emergency")
    clean_urgency = urgency.lower() if urgency.lower() in valid_urgencies else "medium"

    existing_open = get_open_escalation_by_user(
        user_id=user_id, reason_type=reason_type, db_path=db_path
    )
    if existing_open:
        ref_id = existing_open["reference_id"]
        updated_summary = (
            f"{existing_open['issue_summary']} | Additional update: {clean_summary}"
        )
        updated_record = save_escalation(
            reference_id=ref_id,
            user_id=user_id,
            who_needs_help=who_needs_help,
            reason_type=reason_type,
            issue_summary=updated_summary,
            checked_by_agent=clean_checked or existing_open.get("checked_by_agent", ""),
            urgency=clean_urgency,
            preferred_language=preferred_language,
            preferred_contact=preferred_contact,
            status="OPEN",
            db_path=db_path,
        )
        logger.info(
            f"Updated existing open escalation ticket {ref_id} for user {user_id}"
        )

        discord_ok = False
        if updated_record:
            discord_ok = await send_escalation_webhook(updated_record, is_update=True)

        return json.dumps({
            "success": True,
            "reference_id": ref_id,
            "status": "OPEN",
            "urgency": clean_urgency,
            "discord_sent": discord_ok,
            "message": f"I've created your support request. Your ticket number is {ref_id}. A healthcare support person will review it and follow up using your preferred contact method.",
        }, ensure_ascii=False)

    ref_id = _generate_ref_id()

    saved = save_escalation(
        reference_id=ref_id,
        user_id=user_id,
        who_needs_help=who_needs_help,
        reason_type=reason_type,
        issue_summary=clean_summary,
        checked_by_agent=clean_checked,
        urgency=clean_urgency,
        preferred_language=preferred_language,
        preferred_contact=preferred_contact,
        status="OPEN",
        db_path=db_path,
    )

    if not saved:
        return json.dumps({
            "success": False,
            "error": "Failed to create support request due to database error.",
        }, ensure_ascii=False)

    discord_ok = await send_escalation_webhook(saved, is_update=False)

    logger.info(
        f"Successfully created escalation ticket {ref_id} for user {user_id} (Discord sent: {discord_ok})"
    )

    return json.dumps({
        "success": True,
        "reference_id": ref_id,
        "status": "OPEN",
        "urgency": clean_urgency,
        "discord_sent": discord_ok,
        "message": f"I've created your support request. Your ticket number is {ref_id}. A healthcare support person will review it and follow up using your preferred contact method.",
    }, ensure_ascii=False)
