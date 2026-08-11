"""
HealthSaathi Outbound Telephony Package.
Exposes OutboundCallManager, OutboundCallConfig, OutboundCallService, and convenience helper functions.
"""

from .call_manager import (
    OutboundCallManager,
    OutboundCallResult,
    make_outbound_call,
    normalize_sip_destination,
)
from .call_service import OutboundCallService, mask_phone_number
from .config import OutboundCallConfig

__all__ = [
    "OutboundCallConfig",
    "OutboundCallManager",
    "OutboundCallResult",
    "OutboundCallService",
    "make_outbound_call",
    "mask_phone_number",
    "normalize_sip_destination",
]
