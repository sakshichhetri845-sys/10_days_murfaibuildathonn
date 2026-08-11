"""
HTTP REST API Server for Outbound Calling & SQLite Memory Services.
Connects Frontend requests directly to Python Backend & LiveKit Outbound Services.
"""

import logging
from typing import Any

from aiohttp import web

try:
    from src.database import init_db
    from src.memory_service import MemoryService
    from src.telephony.outbound.call_manager import OutboundCallManager
    from src.telephony.outbound.call_service import (
        OutboundCallService,
        mask_phone_number,
    )
    from src.telephony.outbound.config import OutboundCallConfig
except ImportError:
    from database import init_db
    from memory_service import MemoryService
    from telephony.outbound.call_manager import OutboundCallManager
    from telephony.outbound.call_service import OutboundCallService, mask_phone_number
    from telephony.outbound.config import OutboundCallConfig

logger = logging.getLogger("telephony.outbound.api_server")


def make_cors_response(data: Any, status: int = 200) -> web.Response:
    """Helper to return JSON response with CORS headers."""
    return web.json_response(
        data,
        status=status,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )


async def handle_options(request: web.Request) -> web.Response:
    """CORS Preflight handler."""
    return web.Response(
        status=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )


async def handle_outbound_call(request: web.Request) -> web.Response:
    """
    POST /api/outbound/call
    Triggers immediate outbound call dispatch via OutboundCallManager.
    """
    try:
        body = await request.json()
        raw_phone = body.get("phoneNumber", "voiceagentagent")
        user_id = body.get("userId", "riya_verma")

        if (
            not raw_phone
            or not isinstance(raw_phone, str)
            or len(raw_phone.strip()) < 2
        ):
            return make_cors_response(
                {
                    "success": False,
                    "error": "Please provide a valid phone number or Linphone username.",
                },
                status=400,
            )

        destination = raw_phone.strip()

        # Seed sample memory if missing for demo user
        if user_id == "riya_verma" and not MemoryService.get_memory(user_id):
            MemoryService.save_memory(
                user_id=user_id,
                name="Riya Verma",
                ongoing_conditions=["Mild Hypertension"],
                last_triage_outcome="Routine Checkup Advice",
                language_preference="English + Hindi",
            )

        room_name = f"outbound-followup-{user_id}"

        # Create record in SQLite DB
        record = OutboundCallService.create_call_record(
            phone_number=destination,
            room_name=room_name,
            scheduled_time=None,
            timezone="UTC",
            user_id=user_id,
        )

        config = OutboundCallConfig.from_env()
        manager = OutboundCallManager(config=config)

        result = await manager.make_call(
            phone_number=destination,
            room_name=room_name,
            participant_name=f"HealthSaathi Followup ({user_id})",
        )

        if result.success:
            OutboundCallService.update_call_status(
                call_id=record["call_id"],
                status="calling",
                participant_id=result.participant_id,
            )
            return make_cors_response(
                {
                    "success": True,
                    "callId": record["call_id"],
                    "roomName": room_name,
                    "status": "calling",
                    "phoneNumber": destination,
                    "participantId": result.participant_id,
                    "message": f"Outbound call dispatched successfully to '{destination}'!",
                }
            )
        else:
            OutboundCallService.update_call_status(
                call_id=record["call_id"],
                status="failed",
                error_message=result.error,
            )
            return make_cors_response(
                {
                    "success": False,
                    "callId": record["call_id"],
                    "roomName": room_name,
                    "status": "failed",
                    "error": result.error or "Failed to dispatch call",
                },
                status=500,
            )

    except Exception as err:
        logger.error(f"[API Call Handler Error]: {err}", exc_info=True)
        return make_cors_response({"success": False, "error": str(err)}, status=500)


async def handle_schedule_call(request: web.Request) -> web.Response:
    """
    POST /api/outbound/schedule
    Saves scheduled callback in SQLite database.
    """
    try:
        body = await request.json()
        raw_phone = body.get("phoneNumber", "voiceagentagent")
        scheduled_time = body.get("scheduledTime")
        tz = body.get("timezone", "UTC")
        user_id = body.get("userId", "riya_verma")

        if (
            not raw_phone
            or not isinstance(raw_phone, str)
            or len(raw_phone.strip()) < 2
        ):
            return make_cors_response(
                {
                    "success": False,
                    "error": "Please provide a valid phone number or Linphone username.",
                },
                status=400,
            )

        if not scheduled_time:
            return make_cors_response(
                {"success": False, "error": "Please select a scheduled callback time."},
                status=400,
            )

        destination = raw_phone.strip()
        room_name = f"outbound-followup-{user_id}"

        record = OutboundCallService.create_call_record(
            phone_number=destination,
            room_name=room_name,
            scheduled_time=scheduled_time,
            timezone=tz,
            user_id=user_id,
        )

        return make_cors_response(
            {
                "success": True,
                "callId": record["call_id"],
                "roomName": room_name,
                "status": "scheduled",
                "phoneNumber": destination,
                "scheduledTime": scheduled_time,
                "timezone": tz,
                "message": "Outbound call scheduled successfully!",
            }
        )

    except Exception as err:
        logger.error(f"[API Schedule Handler Error]: {err}", exc_info=True)
        return make_cors_response({"success": False, "error": str(err)}, status=500)


async def handle_call_history(request: web.Request) -> web.Response:
    """
    GET /api/outbound/history
    Fetches call history records directly from SQLite database with masked phone numbers.
    """
    try:
        records = OutboundCallService.get_call_history(limit=20)
        history = [
            {
                "callId": r["call_id"],
                "maskedPhoneNumber": mask_phone_number(r["phone_number"]),
                "scheduledTime": r["scheduled_time"] or r["created_at"],
                "timezone": r["timezone"],
                "status": r["status"],
                "createdAt": r["created_at"],
            }
            for r in records
        ]
        return make_cors_response({"success": True, "history": history})
    except Exception as err:
        logger.error(f"[API History Handler Error]: {err}", exc_info=True)
        return make_cors_response({"success": False, "error": str(err)}, status=500)


def create_app() -> web.Application:
    init_db()
    app = web.Application()
    app.router.add_options("/{tail:.*}", handle_options)
    app.router.add_post("/api/outbound/call", handle_outbound_call)
    app.router.add_post("/api/outbound/schedule", handle_schedule_call)
    app.router.add_get("/api/outbound/history", handle_call_history)
    return app


async def start_api_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(
        f"HealthSaathi Outbound HTTP API Server running at http://{host}:{port}"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    web.run_app(app, host="127.0.0.1", port=8000)
