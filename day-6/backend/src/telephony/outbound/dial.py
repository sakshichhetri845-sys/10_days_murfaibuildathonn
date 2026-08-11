"""
Day 6 Outbound CLI Dial Script for HealthSaathi Voice Agent.

Usage:
    uv run python src/telephony/outbound/dial.py --to sakshyambhttr --user-id sakshyam
"""

import argparse
import asyncio
import logging
import sys

try:
    from src.memory_service import MemoryService
    from src.telephony.outbound.call_manager import (
        OutboundCallManager,
        normalize_sip_destination,
    )
    from src.telephony.outbound.config import OutboundCallConfig
except ImportError:
    from memory_service import MemoryService
    from telephony.outbound.call_manager import (
        OutboundCallManager,
        normalize_sip_destination,
    )
    from telephony.outbound.config import OutboundCallConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("healthsathi.day6.dial")


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dial an outbound HealthSaathi follow-up call via LiveKit SIP"
    )
    parser.add_argument(
        "--to",
        "-t",
        default="voiceagentagent",
        help="Destination SIP username (e.g. sakshyambhttr) or phone number",
    )
    parser.add_argument(
        "--user-id",
        "-u",
        default="riya_verma",
        help="Target user_id (default: riya_verma)",
    )
    parser.add_argument(
        "--name",
        "-n",
        default="Riya",
        help="Target user display name (default: Riya)",
    )

    args = parser.parse_args()
    user_id = args.user_id
    dest = normalize_sip_destination(args.to)

    # Seed sample memory if missing
    if not MemoryService.get_memory(user_id):
        MemoryService.save_memory(
            user_id=user_id,
            name=args.name,
            ongoing_conditions=["Mild Hypertension"],
            last_triage_outcome="Routine Checkup Advice",
            language_preference="English + Hindi",
        )

    room_name = f"outbound-followup-{user_id}"

    print("\n========================================================")
    print(" [HealthSaathi] Outbound Telephony CLI Dial")
    print("========================================================")
    print(f"Destination Target : {dest}")
    print(f"Target User ID     : {user_id}")
    print(f"Room Name          : {room_name}")

    try:
        config = OutboundCallConfig.from_env()
        manager = OutboundCallManager(config=config)
        result = await manager.make_call(
            phone_number=dest,
            room_name=room_name,
            participant_name=f"HealthSaathi Caller ({args.name})",
        )

        if result.success:
            print(f"[SUCCESS] Outbound SIP call initiated successfully to '{dest}'!")
            print(f"   Participant ID : {result.participant_id}")
            print(f"   Room Name      : {result.room_name}")
            return 0
        else:
            print(f"[ERROR] Failed to dispatch SIP call: {result.error}")
            return 1
    except Exception as err:
        logger.error(f"Outbound dial error: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
