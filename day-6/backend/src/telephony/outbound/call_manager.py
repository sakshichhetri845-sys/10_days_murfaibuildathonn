"""
Outbound telephony manager for initiating SIP phone calls via LiveKit Server API.
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Optional

from livekit import api
from livekit.protocol.sip import CreateSIPParticipantRequest

from .config import OutboundCallConfig

logger = logging.getLogger("telephony.outbound.call_manager")


@dataclass
class OutboundCallResult:
    success: bool
    room_name: str
    phone_number: str
    participant_id: Optional[str] = None
    participant_identity: Optional[str] = None
    error: Optional[str] = None


def normalize_sip_destination(dest: str) -> str:
    """
    Normalizes outbound destination target for LiveKit SIP API.
    LiveKit expects a phone number (e.g. +15551234567) or bare SIP username (e.g. voiceagentagent).
    """
    cleaned = dest.strip()
    if not cleaned:
        return cleaned
    if cleaned.startswith("sip:"):
        cleaned = cleaned.replace("sip:", "")
    if "@" in cleaned:
        cleaned = cleaned.split("@")[0]
    return cleaned


class OutboundCallManager:
    """
    Manages dispatching outbound phone calls to LiveKit rooms using SIP trunking.
    """

    def __init__(self, config: Optional[OutboundCallConfig] = None) -> None:
        self._config = config or OutboundCallConfig.from_env()

    @property
    def config(self) -> OutboundCallConfig:
        return self._config

    async def make_call(
        self,
        phone_number: str,
        room_name: Optional[str] = None,
        participant_identity: Optional[str] = None,
        participant_name: Optional[str] = None,
        play_dialtone: bool = True,
    ) -> OutboundCallResult:
        """
        Initiates an outbound SIP call to the given phone number and attaches it to a LiveKit room.

        Args:
            phone_number: Target phone number or Linphone SIP username.
            room_name: Optional LiveKit room name. Auto-generated if not provided.
            participant_identity: Optional identity for the phone participant.
            participant_name: Optional display name for the caller.
            play_dialtone: Whether to play a dial tone to other room participants while waiting.

        Returns:
            OutboundCallResult with call dispatch metadata.
        """
        formatted_phone = normalize_sip_destination(phone_number)
        if not formatted_phone:
            return OutboundCallResult(
                success=False,
                room_name=room_name or "",
                phone_number=phone_number,
                error="Phone number or SIP username cannot be empty",
            )

        target_room = room_name or f"outbound-call-{uuid.uuid4().hex[:8]}"
        identity = participant_identity or f"sip_user_{uuid.uuid4().hex[:6]}"
        display_name = participant_name or f"Phone User ({formatted_phone})"

        logger.info(
            "[OutboundCall] Initiating call to %s in room '%s' (Trunk: %s)",
            formatted_phone,
            target_room,
            self.config.sip_trunk_id,
        )

        lkapi = api.LiveKitAPI(
            url=self.config.livekit_url,
            api_key=self.config.api_key,
            api_secret=self.config.api_secret,
        )

        try:
            # 1. Ensure Room exists
            try:
                await lkapi.room.create_room(api.CreateRoomRequest(name=target_room))
                logger.info("[OutboundCall] Room '%s' created or verified", target_room)
            except Exception as re:
                logger.debug(
                    "[OutboundCall] Room creation notice for '%s': %s",
                    target_room,
                    re,
                )

            # 2. Dispatch Outbound Agent Worker to Room FIRST (CRITICAL!)
            try:
                agent_name = os.getenv("OUTBOUND_AGENT_NAME", "outbound-agent")
                user_id_clean = target_room.replace("outbound-followup-", "").replace(
                    "outbound-", ""
                )
                meta_str = json.dumps(
                    {
                        "user_id": user_id_clean,
                        "name": "Riya" if user_id_clean == "riya_verma" else "User",
                        "phone_number": formatted_phone,
                    }
                )
                await lkapi.agent_dispatch.create_dispatch(
                    api.CreateAgentDispatchRequest(
                        agent_name=agent_name,
                        room=target_room,
                        metadata=meta_str,
                    )
                )
                logger.info(
                    "[OutboundCall] Agent worker '%s' dispatched to room '%s'",
                    agent_name,
                    target_room,
                )
            except Exception as de:
                logger.info(
                    "[OutboundCall] Agent dispatch notice for '%s': %s",
                    target_room,
                    de,
                )

            # 3. Create Outbound SIP Participant
            req = CreateSIPParticipantRequest(
                sip_trunk_id=self.config.sip_trunk_id,
                sip_call_to=formatted_phone,
                room_name=target_room,
                participant_identity=identity,
                participant_name=display_name,
                play_dialtone=play_dialtone,
            )

            participant_info = await lkapi.sip.create_sip_participant(req)

            sip_id = str(
                getattr(
                    participant_info,
                    "sip_participant_id",
                    getattr(
                        participant_info,
                        "participant_id",
                        getattr(participant_info, "sid", "PA_sip_call"),
                    ),
                )
            )
            sip_identity = str(
                getattr(
                    participant_info,
                    "participant_identity",
                    getattr(participant_info, "identity", identity),
                )
            )

            logger.info(
                "[OutboundCall] Call dispatched successfully! Participant ID: %s, Identity: %s",
                sip_id,
                sip_identity,
            )

            return OutboundCallResult(
                success=True,
                room_name=target_room,
                phone_number=formatted_phone,
                participant_id=sip_id,
                participant_identity=sip_identity,
            )

        except Exception as e:
            logger.error("[OutboundCall] Failed to place outbound SIP call: %s", e)
            return OutboundCallResult(
                success=False,
                room_name=target_room,
                phone_number=formatted_phone,
                error=str(e),
            )
        finally:
            await lkapi.aclose()


async def make_outbound_call(
    phone_number: str,
    room_name: Optional[str] = None,
    config: Optional[OutboundCallConfig] = None,
) -> OutboundCallResult:
    """Convenience helper function to place an outbound call."""
    manager = OutboundCallManager(config=config)
    return await manager.make_call(phone_number=phone_number, room_name=room_name)
