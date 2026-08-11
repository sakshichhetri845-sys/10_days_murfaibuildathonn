"""
Tests for outbound telephony module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from telephony.outbound import (
    OutboundCallConfig,
    OutboundCallManager,
    OutboundCallResult,
)


def test_outbound_config_missing_env():
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(ValueError, match="LIVEKIT_API_KEY is missing"),
    ):
        OutboundCallConfig.from_env()


def test_outbound_config_valid_env():
    env_vars = {
        "LIVEKIT_URL": "http://localhost:7880",
        "LIVEKIT_API_KEY": "test_key",
        "LIVEKIT_API_SECRET": "test_secret",
        "LIVEKIT_SIP_TRUNK_ID": "ST_test123",
    }
    with patch.dict("os.environ", env_vars, clear=True):
        cfg = OutboundCallConfig.from_env()
        assert cfg.livekit_url == "http://localhost:7880"
        assert cfg.api_key == "test_key"
        assert cfg.api_secret == "test_secret"
        assert cfg.sip_trunk_id == "ST_test123"


@pytest.mark.asyncio
async def test_make_call_empty_phone():
    cfg = OutboundCallConfig(
        livekit_url="http://localhost:7880",
        api_key="test_key",
        api_secret="test_secret",
        sip_trunk_id="ST_test123",
    )
    manager = OutboundCallManager(config=cfg)
    result = await manager.make_call(phone_number="  ")
    assert not result.success
    assert "cannot be empty" in result.error


@pytest.mark.asyncio
async def test_make_call_success():
    cfg = OutboundCallConfig(
        livekit_url="http://localhost:7880",
        api_key="test_key",
        api_secret="test_secret",
        sip_trunk_id="ST_test123",
    )
    manager = OutboundCallManager(config=cfg)

    mock_participant = MagicMock()
    mock_participant.sip_participant_id = "PA_123456"
    mock_participant.sid = "PA_123456"
    mock_participant.participant_identity = "sip_user_test"
    mock_participant.identity = "sip_user_test"

    mock_sip_api = MagicMock()
    mock_sip_api.create_sip_participant = AsyncMock(return_value=mock_participant)

    mock_lkapi = MagicMock()
    mock_lkapi.sip = mock_sip_api
    mock_lkapi.aclose = AsyncMock()

    with patch("livekit.api.LiveKitAPI", return_value=mock_lkapi):
        result: OutboundCallResult = await manager.make_call(
            phone_number="+15551234567",
            room_name="test-room",
        )

        assert result.success
        assert result.room_name == "test-room"
        assert result.participant_id == "PA_123456"
        assert result.participant_identity == "sip_user_test"
        mock_sip_api.create_sip_participant.assert_called_once()
        mock_lkapi.aclose.assert_called_once()
