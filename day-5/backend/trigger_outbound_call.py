"""
Day 6 Outbound Call Trigger Script for HealthSaathi Voice Agent.

Usage:
    python trigger_outbound_call.py [--user riya_verma] [--phone +15551234567]
"""

import argparse
import asyncio
import logging
import sys

try:
    from src.memory_service import MemoryService
    from src.telephony.outbound.call_manager import OutboundCallManager
    from src.telephony.outbound.config import OutboundCallConfig
except ImportError:
    from memory_service import MemoryService
    from telephony.outbound.call_manager import OutboundCallManager
    from telephony.outbound.config import OutboundCallConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("healthsathi.day6.trigger")


def seed_sample_memory(user_id: str) -> None:
    """Pre-seed sample memory for Day 6 follow-up demo if missing."""
    existing = MemoryService.get_memory(user_id)
    if not existing:
        logger.info(f"Pre-seeding SQLite memory for user: {user_id}")
        MemoryService.save_memory(
            user_id=user_id,
            name="Riya Verma",
            ongoing_conditions=["Mild Hypertension"],
            last_triage_outcome="Routine Checkup Advice",
            language_preference="English + Hindi",
        )
    else:
        logger.info(f"SQLite memory already exists for user: {user_id}")


async def trigger_outbound_session(
    user_id: str, phone_number: str | None = None
) -> int:
    seed_sample_memory(user_id)

    room_name = f"outbound-followup-{user_id}"

    print("\n========================================================")
    print(" [HealthSaathi] Day 6 Outbound Follow-up Call Trigger")
    print("========================================================")
    print(f"Target User ID : {user_id}")
    print(f"Room Name      : {room_name}")

    if phone_number:
        print(f"Phone Number   : {phone_number}")
        try:
            config = OutboundCallConfig.from_env()
            manager = OutboundCallManager(config=config)
            result = await manager.make_call(
                phone_number=phone_number,
                room_name=room_name,
                participant_name=f"HealthSaathi Followup ({user_id})",
            )

            if result.success:
                print("[SUCCESS] Outbound SIP call initiated successfully!")
                print(f"   Participant ID: {result.participant_id}")
                return 0
            else:
                print(f"[NOTICE] SIP Call dispatch notice: {result.error}")
                print(
                    "   Agent can still connect to the room directly for dev testing."
                )
                return 0
        except Exception as err:
            logger.warning(
                f"LiveKit SIP credentials incomplete ({err}). Demonstrating room trigger:"
            )
    else:
        print(
            "[INFO] No phone number specified. Triggering room dispatch for agent testing."
        )

    print("\n[READY] Day 6 Room Ready!")
    print(f"   Connect your agent and frontend client to room: '{room_name}'")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trigger a Day 6 HealthSaathi outbound follow-up session"
    )
    parser.add_argument(
        "--user",
        "-u",
        default="riya_verma",
        help="Target user_id (default: riya_verma)",
    )
    parser.add_argument(
        "--phone",
        "-p",
        default=None,
        help="Optional destination phone number or Linphone SIP username",
    )
    parser.add_argument(
        "--linphone",
        "-l",
        default=None,
        help="Optional Linphone SIP username (e.g. voiceagentagent)",
    )

    args = parser.parse_args()
    target_dest = args.linphone or args.phone or "voiceagentagent"

    sys.exit(
        asyncio.run(
            trigger_outbound_session(user_id=args.user, phone_number=target_dest)
        )
    )


if __name__ == "__main__":
    main()
