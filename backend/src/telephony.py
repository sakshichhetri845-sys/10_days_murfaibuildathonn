"""
Telephony and Outbound Calling Foundation for BolBuddy Voice Agent.

Uses LiveKit Telephony / SIP Outbound API to initiate phone calls to learners.
Reads all credentials from environment variables without hardcoding secrets.
"""

import json
import logging
import os
import re
from typing import Any

from livekit.api import CreateSIPParticipantRequest, LiveKitAPI

logger = logging.getLogger("agent.telephony")


class TelephonyConfigurationError(Exception):
    """Raised when telephony initialization fails due to missing or invalid configuration."""

    pass


def get_telephony_config() -> dict[str, Any]:
    """
    Retrieve and validate telephony configuration from environment variables.
    Never exposes secret values directly in logs.
    """
    livekit_url = os.getenv("LIVEKIT_URL", "").strip()
    api_key = os.getenv("LIVEKIT_API_KEY", "").strip()
    api_secret = os.getenv("LIVEKIT_API_SECRET", "").strip()
    sip_trunk_id = (
        os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID", "").strip()
        or os.getenv("LIVEKIT_SIP_TRUNK_ID", "").strip()
    )

    # Linphone SIP configuration (sip.linphone.org)
    linphone_user = os.getenv("LINPHONE_USERNAME", "").strip() or os.getenv("SIP_USERNAME", "").strip()
    linphone_domain = os.getenv("LINPHONE_DOMAIN", "sip.linphone.org").strip()
    linphone_caller_id = (
        os.getenv("LINPHONE_CALLER_ID", "").strip()
        or os.getenv("SIP_CALLER_ID", "").strip()
        or (f"sip:{linphone_user}@{linphone_domain}" if linphone_user else "")
    )

    # Legacy Twilio configuration fallback
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    twilio_auth = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    twilio_phone = os.getenv("TWILIO_PHONE_NUMBER", "").strip()

    enabled = os.getenv("OUTBOUND_CALL_ENABLED", "true").strip().lower() in (
        "true",
        "1",
        "yes",
    )

    missing = []
    if not livekit_url:
        missing.append("LIVEKIT_URL")
    if not api_key:
        missing.append("LIVEKIT_API_KEY")
    if not api_secret:
        missing.append("LIVEKIT_API_SECRET")
    if not sip_trunk_id:
        missing.append("LIVEKIT_SIP_TRUNK_ID")

    return {
        "livekit_url": livekit_url,
        "api_key": api_key,
        "api_secret": api_secret,
        "sip_trunk_id": sip_trunk_id,
        "linphone_username": linphone_user,
        "linphone_domain": linphone_domain,
        "linphone_caller_id": linphone_caller_id,
        "twilio_account_sid": twilio_sid,
        "twilio_auth_token": twilio_auth,
        "twilio_phone_number": twilio_phone,
        "enabled": enabled,
        "is_configured": len(missing) == 0,
        "missing_vars": missing,
    }


def mask_phone_number(phone_number: str) -> str:
    """Mask phone number for safe logging (e.g., '+9198******10')."""
    if not phone_number:
        return ""
    clean = re.sub(r"[^\d+]", "", phone_number)
    if len(clean) <= 5:
        return "***"
    return f"{clean[:4]}****{clean[-2:]}"


def build_outbound_sip_request(
    phone_number: str,
    room_name: str,
    user_id: str,
    user_name: str = "",
    sip_trunk_id: str = "",
) -> CreateSIPParticipantRequest:
    """
    Construct a LiveKit CreateSIPParticipantRequest for initiating an outbound phone call.
    Validates phone number and parameters.
    """
    if not phone_number or not phone_number.strip():
        raise ValueError("phone_number must be provided for outbound calls.")

    if not room_name or not room_name.strip():
        raise ValueError("room_name must be provided for outbound calls.")

    if not user_id or not user_id.strip():
        raise ValueError("user_id must be provided for outbound calls.")

    config = get_telephony_config()
    active_trunk_id = sip_trunk_id or config["sip_trunk_id"]

    if not active_trunk_id:
        raise TelephonyConfigurationError(
            "LIVEKIT_SIP_TRUNK_ID is missing in environment variables or parameters."
        )

    # Format participant identity & metadata for LiveKit SIP room dispatch
    metadata = json.dumps(
        {
            "is_outbound": True,
            "user_id": user_id,
            "name": user_name,
            "phone_number_masked": mask_phone_number(phone_number),
        }
    )

    attributes = {
        "user_id": user_id,
        "is_outbound": "true",
        "name": user_name,
    }

    raw_sip_number = (
        config.get("linphone_username")
        or config.get("linphone_caller_id")
        or config.get("twilio_phone_number")
        or os.getenv("SIP_CALLER_ID", "").strip()
    )
    clean_sip_number = raw_sip_number.strip()
    if clean_sip_number.lower().startswith("sip:"):
        clean_sip_number = clean_sip_number[4:]
    if "@" in clean_sip_number:
        clean_sip_number = clean_sip_number.split("@")[0]

    clean_call_to = phone_number.strip()
    if clean_call_to.lower().startswith("sip:"):
        clean_call_to = clean_call_to[4:]
    if "@" in clean_call_to:
        clean_call_to = clean_call_to.split("@")[0]

    req_kwargs = {
        "sip_trunk_id": active_trunk_id,
        "sip_call_to": clean_call_to,
        "room_name": room_name.strip(),
        "participant_identity": user_id.strip(),
        "participant_name": user_name.strip() or f"User_{user_id}",
        "participant_metadata": metadata,
        "participant_attributes": attributes,
        "play_ringtone": True,
        "wait_until_answered": False,
    }
    if clean_sip_number:
        req_kwargs["sip_number"] = clean_sip_number

    return CreateSIPParticipantRequest(**req_kwargs)


async def initiate_outbound_call(
    phone_number: str,
    room_name: str,
    user_id: str,
    user_name: str = "",
) -> dict[str, Any]:
    """
    Initiate an outbound phone call via LiveKit Telephony API.
    Does NOT fabricate successful responses if credentials are missing.
    """
    config = get_telephony_config()

    if not config["enabled"]:
        raise TelephonyConfigurationError(
            "Outbound calling is currently disabled (OUTBOUND_CALL_ENABLED=false)."
        )

    if not config["is_configured"]:
        if "LIVEKIT_SIP_TRUNK_ID" in config["missing_vars"]:
            raise TelephonyConfigurationError(
                "NVIDIA LLM is configured, but outbound calling requires LIVEKIT_SIP_TRUNK_ID."
            )
        missing_str = ", ".join(config["missing_vars"])
        raise TelephonyConfigurationError(
            f"Telephony integration cannot initiate call. Missing configuration environment variables: {missing_str}"
        )

    req = build_outbound_sip_request(
        phone_number=phone_number,
        room_name=room_name,
        user_id=user_id,
        user_name=user_name,
        sip_trunk_id=config["sip_trunk_id"],
    )

    masked_phone = mask_phone_number(phone_number)
    logger.info(
        f"Initiating outbound SIP call to {masked_phone} in room {room_name} for user_id '{user_id}'"
    )

    async with LiveKitAPI(
        url=config["livekit_url"],
        api_key=config["api_key"],
        api_secret=config["api_secret"],
    ) as api:
        sip_participant = await api.sip.create_sip_participant(req)
        logger.info(
            f"SIP call requested successfully for room {room_name}, participant: {sip_participant}"
        )
        return {
            "status": "INITIATED",
            "room_name": room_name,
            "user_id": user_id,
            "phone_number_masked": masked_phone,
            "participant_info": str(sip_participant),
        }
