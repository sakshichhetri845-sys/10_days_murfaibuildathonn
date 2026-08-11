"""
Tests for LiveKit Telephony / Outbound Calling Configuration Foundation.
"""

import pytest
from livekit.api import CreateSIPParticipantRequest

from telephony import (
    TelephonyConfigurationError,
    build_outbound_sip_request,
    get_telephony_config,
    initiate_outbound_call,
    mask_phone_number,
)


def test_telephony_imports():
    """Verify telephony module imports cleanly."""
    assert get_telephony_config is not None
    assert build_outbound_sip_request is not None
    assert mask_phone_number is not None


def test_phone_number_masking():
    """Verify phone numbers are properly masked to prevent exposing raw credentials in logs."""
    assert mask_phone_number("+919876543210") == "+919****10"
    assert mask_phone_number("+12025550123") == "+120****23"
    assert mask_phone_number("") == ""
    assert mask_phone_number("123") == "***"


def test_telephony_config_missing_vars(monkeypatch):
    """Verify configuration detects missing required environment variables."""
    monkeypatch.delenv("LIVEKIT_SIP_TRUNK_ID", raising=False)
    monkeypatch.setenv("LIVEKIT_URL", "wss://test.livekit.cloud")
    monkeypatch.setenv("LIVEKIT_API_KEY", "test_key")
    monkeypatch.setenv("LIVEKIT_API_SECRET", "test_secret")

    config = get_telephony_config()
    assert config["is_configured"] is False
    assert "LIVEKIT_SIP_TRUNK_ID" in config["missing_vars"]


def test_build_outbound_sip_request_valid(monkeypatch):
    """Verify CreateSIPParticipantRequest is constructed accurately."""
    monkeypatch.setenv("LIVEKIT_SIP_TRUNK_ID", "ST_TEST_TRUNK_123")
    monkeypatch.setenv("LIVEKIT_URL", "wss://test.livekit.cloud")
    monkeypatch.setenv("LIVEKIT_API_KEY", "test_key")
    monkeypatch.setenv("LIVEKIT_API_SECRET", "test_secret")

    req = build_outbound_sip_request(
        phone_number="+919876543210",
        room_name="test_practice_room",
        user_id="user_test_1",
        user_name="Sakshyam",
    )

    assert isinstance(req, CreateSIPParticipantRequest)
    assert req.sip_trunk_id == "ST_TEST_TRUNK_123"
    assert req.sip_call_to == "+919876543210"
    assert req.room_name == "test_practice_room"
    assert req.participant_identity == "user_test_1"
    assert req.participant_name == "Sakshyam"
    assert "user_test_1" in req.participant_metadata
    assert req.participant_attributes["user_id"] == "user_test_1"
    assert req.participant_attributes["is_outbound"] == "true"


def test_build_outbound_sip_request_missing_trunk(monkeypatch):
    """Verify build_outbound_sip_request raises TelephonyConfigurationError if trunk ID is missing."""
    monkeypatch.delenv("LIVEKIT_SIP_TRUNK_ID", raising=False)

    with pytest.raises(TelephonyConfigurationError) as exc_info:
        build_outbound_sip_request(
            phone_number="+919876543210",
            room_name="test_room",
            user_id="user_1",
        )
    assert "LIVEKIT_SIP_TRUNK_ID is missing" in str(exc_info.value)


@pytest.mark.asyncio
async def test_initiate_outbound_call_raises_when_unconfigured(monkeypatch):
    """Verify initiate_outbound_call refuses to fake calls when credentials are missing."""
    monkeypatch.delenv("LIVEKIT_SIP_TRUNK_ID", raising=False)

    with pytest.raises(TelephonyConfigurationError) as exc_info:
        await initiate_outbound_call(
            phone_number="+919876543210",
            room_name="test_room",
            user_id="user_1",
        )
    assert "LIVEKIT_SIP_TRUNK_ID" in str(exc_info.value)
