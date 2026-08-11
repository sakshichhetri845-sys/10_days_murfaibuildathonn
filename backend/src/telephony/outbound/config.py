"""
Outbound telephony configuration loader.
Extracts and validates environment variables required for LiveKit SIP outbound calling.
"""

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger("telephony.outbound.config")

# Load environment variables from .env.local if present
load_dotenv(".env.local")
load_dotenv(".env")


@dataclass
class OutboundCallConfig:
    livekit_url: str
    api_key: str
    api_secret: str
    sip_trunk_id: str

    @classmethod
    def from_env(cls) -> "OutboundCallConfig":
        """
        Loads configuration from environment variables.
        Raises ValueError if required parameters are missing.
        """
        livekit_url = os.getenv("LIVEKIT_URL", "http://localhost:7880")
        api_key = os.getenv("LIVEKIT_API_KEY", "")
        api_secret = os.getenv("LIVEKIT_API_SECRET", "")
        sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID") or os.getenv(
            "LIVEKIT_SIP_OUTBOUND_TRUNK_ID", ""
        )

        errors = []
        if not api_key:
            errors.append("LIVEKIT_API_KEY is missing")
        if not api_secret:
            errors.append("LIVEKIT_API_SECRET is missing")
        if not sip_trunk_id:
            errors.append("LIVEKIT_SIP_TRUNK_ID is missing")

        if errors:
            err_msg = (
                "Outbound telephony configuration incomplete: "
                + ", ".join(errors)
                + ". Please set them in backend/.env.local."
            )
            logger.error(err_msg)
            raise ValueError(err_msg)

        return cls(
            livekit_url=livekit_url,
            api_key=api_key,
            api_secret=api_secret,
            sip_trunk_id=sip_trunk_id,
        )
