"""Trigger an outbound call for BolBuddy.

Dispatches the outbound BolBuddy agent into a room with phone number and learner metadata attached.

Usage:

    uv run python src/telephony/outbound/agent.py dev

Then trigger a call from another terminal:

    uv run python src/telephony/outbound/dial.py --to +9779876543210 --user-id sakshyam
"""

import argparse
import asyncio
import json
import os
import re
import sys
import uuid

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

# Must match the agent_name in agent.py.
AGENT_NAME = "outbound-agent"

# E.164: a leading + and 7-15 digits, e.g. +15551234567.
E164 = re.compile(r"^\+[1-9]\d{6,14}$")


async def dial(phone_number: str, room_name: str, user_id: str = "default_user", name: str = "") -> None:
    """Create the room and dispatch the outbound agent into it."""
    lk = api.LiveKitAPI()
    try:
        await lk.room.create_room(api.CreateRoomRequest(name=room_name))

        metadata = json.dumps({
            "phone_number": phone_number,
            "user_id": user_id,
            "name": name,
        })

        # The agent reads this metadata to know who to call.
        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=metadata,
            )
        )
    finally:
        await lk.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Place an outbound BolBuddy practice call.")
    parser.add_argument(
        "--to",
        required=True,
        help="Number to call, in E.164 format (e.g. +9779876543210)",
    )
    parser.add_argument(
        "--user-id",
        "--learner",
        dest="user_id",
        default="default_user",
        help="Learner user_id to load persistent memory context.",
    )
    parser.add_argument(
        "--name",
        default="",
        help="Learner name.",
    )
    parser.add_argument(
        "--room",
        default=None,
        help="Room name to use. Defaults to a generated one.",
    )
    args = parser.parse_args()

    target_destination = args.to.strip()
    linphone_domain = os.getenv("LINPHONE_DOMAIN", "sip.linphone.org").strip()
    if not target_destination.startswith("+") and not target_destination.startswith("sip:"):
        if "@" in target_destination:
            target_destination = f"sip:{target_destination}"
        else:
            target_destination = f"sip:{target_destination}@{linphone_domain}"

    room_name = args.room or f"outbound-{uuid.uuid4().hex[:8]}"

    asyncio.run(dial(target_destination, room_name, user_id=args.user_id, name=args.name))

    print(f"Dispatched {AGENT_NAME} to room '{room_name}' to call '{target_destination}' for learner '{args.user_id}'.")
    print("Watch the worker terminal for call progress.")


if __name__ == "__main__":
    main()
