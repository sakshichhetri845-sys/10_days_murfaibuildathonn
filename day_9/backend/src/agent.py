# ruff: noqa: E402
import asyncio
import json
import logging
import os
import re

import httpx
from dotenv import load_dotenv

# Ensure environment variables from backend/.env.local are eagerly loaded
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_backend_dir, ".env.local"))
load_dotenv(os.path.join(_backend_dir, ".env"))
load_dotenv(".env.local")
load_dotenv()

# pyrefly: ignore [missing-import]
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    llm,
    tokenize,
)
from livekit.agents.job import JobExecutorType

# pyrefly: ignore [missing-import]
from livekit.plugins import deepgram, google, murf, openai, silero

from db import (
    get_nearby_facilities,
    get_or_create_user,
    init_db,
    save_call_analytics,
)
from escalation_tools import (
    create_escalation as fn_create_escalation,
)
from memory_tools import (
    async_prefetch_user_memory,
)
from memory_tools import (
    forget_my_data as fn_forget_my_data,
)
from memory_tools import (
    lookup_user_memory as fn_lookup_user_memory,
)
from memory_tools import (
    save_user_memory as fn_save_user_memory,
)
from memory_tools import (
    what_do_you_remember as fn_what_do_you_remember,
)
from prompts.clinic_sathi import CLINIC_SATHI_PROMPT
from prompts.system_prompt import SYSTEM_PROMPT
from rag import search_health_resources as fn_search_health_resources

logger = logging.getLogger("agent")


def _prune_history(session: AgentSession, max_turns: int = 6) -> None:
    """Keep system prompt + most recent max_turns messages and filter out raw function JSON leakage."""
    try:
        if (
            hasattr(session, "chat_ctx")
            and session.chat_ctx
            and hasattr(session.chat_ctx, "messages")
        ):
            msgs = session.chat_ctx.messages
            cleaned_msgs = []
            for m in msgs:
                content = str(getattr(m, "content", "") or "")
                if (
                    '{"name":' in content
                    or '{"who_needs_help"' in content
                    or '"parameters":' in content
                    or "</function>" in content
                    or "<tool_call>" in content
                    or "create_escalation" in content
                    or "find_nearby_facility>" in content
                    or "symptom_to_triage>" in content
                    or (">" in content and "{" in content)
                ):
                    clean_content = re.sub(
                        r"\b\w+>\s*\{[^}]*\}?", "", content
                    )
                    clean_content = re.sub(
                        r"<\/?(?:tool_call|function)[^>]*>", "", clean_content
                    )
                    clean_content = re.sub(
                        r"\{\s*\"[^\"]+\"\s*:[\s\S]*?\}", "", clean_content
                    ).strip()
                    if not clean_content or clean_content.startswith("{"):
                        continue
                    if hasattr(m, "content"):
                        m.content = clean_content
                cleaned_msgs.append(m)

            if len(cleaned_msgs) > max_turns + 1:
                system_msg = (
                    [cleaned_msgs[0]]
                    if (
                        cleaned_msgs
                        and getattr(cleaned_msgs[0], "role", None)
                        in ("system", "developer")
                    )
                    else []
                )
                recent_msgs = cleaned_msgs[-max_turns:]
                session.chat_ctx.messages = system_msg + [
                    m for m in recent_msgs if m not in system_msg
                ]
            else:
                session.chat_ctx.messages = cleaned_msgs
    except Exception as e:
        logger.warning(f"Chat context pruning exception: {e}")


# ---------------------------------------------------------------------------
# Triage levels — coarse classification for safe, non-diagnostic guidance
# ---------------------------------------------------------------------------
_TRIAGE_GUIDANCE: dict[str, dict[str, str]] = {
    "self_care": {
        "label": "Self-care",
        "advice": (
            "This sounds like it can be managed at home with rest, fluids, and over-the-counter "
            "remedies. Monitor closely — if symptoms worsen or persist beyond 3 days, please "
            "visit a clinic."
        ),
    },
    "routine": {
        "label": "Routine care",
        "advice": (
            "A visit to a local health post or PHC in the next few days would be helpful. "
            "There is no immediate emergency, but don't delay too long."
        ),
    },
    "soon": {
        "label": "See a doctor soon",
        "advice": (
            "Please visit a clinic or PHC today or tomorrow. This shouldn't wait more than "
            "24-48 hours."
        ),
    },
    "urgent": {
        "label": "Urgent care needed",
        "advice": (
            "Please go to the nearest hospital or emergency department as soon as possible, "
            "or call 112 for emergency services."
        ),
    },
}

_URGENT_KEYWORDS = {
    "chest pain",
    "difficulty breathing",
    "can't breathe",
    "unconscious",
    "severe bleeding",
    "stroke",
    "heart attack",
    "seizure",
    "convulsion",
    "not breathing",
    "no pulse",
}
_SOON_KEYWORDS = {
    "high fever",
    "103",
    "104",
    "vomiting blood",
    "blood in stool",
    "severe pain",
    "confusion",
    "disoriented",
    "can't walk",
    "dehydrated",
}
_ROUTINE_KEYWORDS = {
    "fever",
    "cough",
    "cold",
    "rash",
    "stomach ache",
    "headache",
    "diarrhea",
    "sore throat",
    "ear pain",
    "eye pain",
}


def _classify_symptoms(symptoms_text: str) -> str:
    """Simple keyword-based pre-classifier. Returns triage level string."""
    lower = symptoms_text.lower()
    for kw in _URGENT_KEYWORDS:
        if kw in lower:
            return "urgent"
    for kw in _SOON_KEYWORDS:
        if kw in lower:
            return "soon"
    for kw in _ROUTINE_KEYWORDS:
        if kw in lower:
            return "routine"
    return "self_care"


def update_current_call_outcome(
    context: RunContext, outcome_type: str, outcome: str = "successful"
) -> None:
    """Update call outcome state for active session based on workflow priority."""
    try:
        sess = getattr(context, "session", None)
        call_state = None
        if sess:
            try:
                ud = getattr(sess, "userdata", None)
                if isinstance(ud, dict):
                    call_state = ud.get("call_state")
            except Exception:
                pass

        if (
            not call_state
            and hasattr(context, "proc")
            and hasattr(context.proc, "userdata")
        ):
            call_state = context.proc.userdata.get("call_state")

        if call_state:
            hierarchy = {
                "HUMAN_ESCALATION": 4,
                "FACILITY_FOUND": 3,
                "TRIAGE_COMPLETED": 2,
                "GENERAL_GUIDANCE": 1,
                "INCOMPLETE": 0,
                "TECHNICAL_ERROR": -1,
            }
            current_type = call_state.get("outcome_type", "INCOMPLETE")
            current_level = hierarchy.get(current_type, 0)
            new_level = hierarchy.get(outcome_type, 0)

            if new_level >= current_level or outcome == "failed":
                call_state["outcome"] = outcome
                call_state["outcome_type"] = outcome_type
                logger.info(f"Updated session call outcome: {outcome} ({outcome_type})")
                try:
                    import time

                    duration = max(
                        1, int(time.time() - call_state.get("start_time", time.time()))
                    )
                    save_call_analytics(
                        session_id=call_state["session_id"],
                        duration=duration,
                        channel=call_state.get("channel", "browser"),
                        outcome=outcome,
                        outcome_type=outcome_type,
                    )
                except Exception as save_err:
                    logger.warning(f"Real-time analytics save warning: {save_err}")
    except Exception as e:
        logger.warning(f"Failed to update call outcome: {e}")


# ---------------------------------------------------------------------------
# MAIN AGENT: HealthSathi (Murf Falcon · Samar)
# ---------------------------------------------------------------------------
class Assistant(Agent):
    """
    HealthSathi — General health-access voice companion.
    Handles general health inquiries, symptom triage, memory, and transfers
    to ClinicSathi when user requests facility/appointment assistance.
    """

    def __init__(self, chat_ctx: llm.ChatContext | None = None) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            chat_ctx=chat_ctx,
            tts=murf.TTS(
                voice="Samar",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
                text_pacing=True,
            ),
        )

    async def on_enter(self) -> None:
        logger.info("Entering HealthSathi (voice: Murf Falcon · Samar)")
        try:
            if (
                hasattr(self, "session")
                and self.session
                and hasattr(self.session, "room_io")
            ):
                room = getattr(self.session.room_io, "room", None)
                if (
                    room
                    and hasattr(room, "local_participant")
                    and room.local_participant
                ):
                    self._attr_task = asyncio.create_task(
                        room.local_participant.set_attributes(
                            {
                                "agent_name": "HealthSathi",
                                "agent_title": "General Health Support",
                                "voice_name": "Murf Falcon · Samar",
                            }
                        )
                    )
        except Exception as e:
            logger.debug(f"Attribute update notice: {e}")

    @function_tool
    async def transfer_to_clinic_sathi(
        self,
        context: RunContext,
        reason: str = "facility_or_appointment_guidance",
    ) -> tuple[Agent, str]:
        """
        Transfer the conversation to ClinicSathi, the healthcare facility and appointment specialist.
        CRITICAL: ONLY invoke this tool AFTER the user explicitly agrees/confirms to be connected with ClinicSathi.
        DO NOT invoke if the user has not confirmed or declined.
        """
        logger.info(f"TOOL CALL: transfer_to_clinic_sathi (reason='{reason}')")
        chat_ctx = self.chat_ctx.copy(exclude_instructions=True)
        specialist = ClinicSathi(chat_ctx=chat_ctx)
        logger.info(
            "TOOL COMPLETE: transfer_to_clinic_sathi -> switching to ClinicSathi"
        )
        return specialist, "Connecting to ClinicSathi..."

    @function_tool
    async def lookup_user_memory(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Look up saved user memory facts. Use only when needed to retrieve saved memory."""
        logger.info("TOOL CALL: lookup_user_memory")
        res = await fn_lookup_user_memory(context, user_id=user_id)
        logger.info("TOOL COMPLETE: lookup_user_memory")
        return res

    @function_tool
    async def save_user_memory(
        self,
        context: RunContext,
        name: str = "",
        language_preference: str = "",
        reminder_preference: str = "",
        contact_preference: str = "",
        user_id: str = "",
    ) -> str:
        """Save user memory facts (name, language, reminder preference, contact preference). Requires user consent."""
        logger.info(
            f"TOOL CALL: save_user_memory (name='{name}', reminder='{reminder_preference}')"
        )
        res = await fn_save_user_memory(
            context,
            name=name,
            language_preference=language_preference,
            reminder_preference=reminder_preference,
            contact_preference=contact_preference,
            user_id=user_id,
        )
        logger.info(f"TOOL COMPLETE: save_user_memory -> {res}")
        return res

    @function_tool
    async def forget_my_data(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Permanently delete saved user memory. Call ONLY AFTER the user gives explicit verbal confirmation (e.g. 'Yes', 'Delete it'). DO NOT invoke unless user has explicitly confirmed deletion."""
        logger.info(f"TOOL CALL: forget_my_data (user_id='{user_id}')")
        res = await fn_forget_my_data(context, user_id=user_id)
        logger.info(f"TOOL COMPLETE: forget_my_data -> {res}")
        return res

    @function_tool
    async def what_do_you_remember(
        self,
        context: RunContext,
        user_id: str = "",
    ) -> str:
        """Summarize saved user memory. Use only when user explicitly asks what is remembered."""
        logger.info(f"TOOL CALL: what_do_you_remember (user_id='{user_id}')")
        res = await fn_what_do_you_remember(context, user_id=user_id)
        logger.info("TOOL COMPLETE: what_do_you_remember")
        return res

    @function_tool
    async def search_health_resources(
        self,
        context: RunContext,
        query: str = "",
    ) -> str:
        """Search health information resources for symptom guidance, doctor visit prep, or general wellness advice."""
        logger.info(f"TOOL CALL: search_health_resources (query='{query}')")
        try:
            res = await fn_search_health_resources(context, query=query)
            update_current_call_outcome(context, "GENERAL_GUIDANCE", "successful")
            logger.info("TOOL COMPLETE: search_health_resources")
            return res
        except Exception as e:
            logger.error(f"TOOL ERROR in search_health_resources: {e}")
            update_current_call_outcome(context, "TECHNICAL_ERROR", "failed")
            raise

    @function_tool
    async def symptom_to_triage(
        self,
        context: RunContext,
        symptoms: str = "",
        duration_days: int = 0,
        severity: str = "mild",
    ) -> str:
        """
        Classify the user's reported symptoms into a safe triage level and recommend
        the appropriate next step.

        IMPORTANT RULES:
        - Do NOT diagnose any medical condition.
        - Do NOT prescribe or recommend specific medications.
        - Do NOT claim medical certainty.
        - Use simple triage levels: self_care, routine, soon, urgent.

        Parameters:
            symptoms: Free-text description of the user's symptoms.
            duration_days: How many days the symptoms have been present (0 = unknown).
            severity: User's self-reported severity — 'mild', 'moderate', or 'severe'.
        """
        try:
            if not symptoms.strip():
                return json.dumps(
                    {
                        "level": "unknown",
                        "label": "Insufficient information",
                        "advice": "Please describe your symptoms so I can help you better.",
                    }
                )

            level = _classify_symptoms(symptoms)

            if severity == "severe" and level in ("self_care", "routine"):
                level = "soon"
            if severity == "severe" and level == "soon":
                level = "urgent"
            if duration_days >= 7 and level == "self_care":
                level = "routine"

            guidance = _TRIAGE_GUIDANCE[level]
            result = {
                "level": level,
                "label": guidance["label"],
                "advice": guidance["advice"],
                "disclaimer": (
                    "HealthSathi is not a doctor. This guidance is for general information only. "
                    "Always consult a qualified healthcare provider for medical decisions."
                ),
            }
            update_current_call_outcome(context, "TRIAGE_COMPLETED", "successful")
            logger.info(
                f"TOOL CALL: symptom_to_triage → level='{level}' "
                f"(symptoms='{symptoms[:60]}...', severity='{severity}', days={duration_days})"
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            logger.error(f"TOOL ERROR in symptom_to_triage: {e}")
            update_current_call_outcome(context, "TECHNICAL_ERROR", "failed")
            raise

    async def end_call(
        self,
        context: RunContext,
        reason: str = "DECLINED",
    ) -> str:
        """End the outbound call session cleanly after user declines or asks to disconnect."""
        logger.info(f"TOOL CALL: end_call (reason='{reason}')")
        try:
            sess = getattr(context, "session", None)
            if sess:
                room_io = getattr(sess, "room_io", None)
                if room_io and hasattr(room_io, "room") and room_io.room:

                    async def _disconnect_delay():
                        await asyncio.sleep(2.5)
                        try:
                            await room_io.room.disconnect()
                        except Exception as disc_err:
                            logger.warning(f"Disconnect error: {disc_err}")

                    disc_task = asyncio.create_task(_disconnect_delay())
                    if hasattr(sess, "userdata") and isinstance(sess.userdata, dict):
                        sess.userdata["disc_task"] = disc_task
        except Exception as e:
            logger.warning(f"Failed to schedule room disconnect: {e}")
        return f"Call ended gracefully ({reason})."

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        user_confirmed_consent: bool = False,
        reason_type: str = "health_concern",
        issue_summary: str = "User requested human health support",
        urgency: str = "medium",
    ) -> str:
        """Submit a human health support request.
        CRITICAL: ONLY invoke this tool AFTER the user explicitly says YES/Sure to submitting a support ticket.
        NEVER invoke this tool if the user is asking a question (e.g. 'What is your escalation process?'), asking for information, or has not yet agreed to submit a request.
        RETURNS: JSON containing `reference_id` (e.g. HS-4821) and `status`.
        RESPONSE RULE: Speak the exact returned `reference_id` to the user.
        """
        logger.info(
            f"TOOL CALL: create_escalation (consent={user_confirmed_consent}, reason='{reason_type}', urgency='{urgency}')"
        )
        try:
            res = await fn_create_escalation(
                context=context,
                user_confirmed_consent=user_confirmed_consent,
                reason_type=reason_type,
                issue_summary=issue_summary,
                urgency=urgency,
            )
            update_current_call_outcome(context, "HUMAN_ESCALATION", "successful")
            logger.info(f"TOOL COMPLETE: create_escalation -> {res}")
            return res
        except Exception as e:
            logger.error(f"TOOL ERROR in create_escalation: {e}")
            update_current_call_outcome(context, "TECHNICAL_ERROR", "failed")
            raise


# ---------------------------------------------------------------------------
# SPECIALIST AGENT: ClinicSathi (Murf Falcon · Pooja)
# ---------------------------------------------------------------------------
class ClinicSathi(Agent):
    """
    ClinicSathi — Healthcare Facility & Appointment Specialist voice companion.
    Focused on helping users find facilities (PHCs, hospitals, clinics) and prepare
    for doctor appointments. Shares conversation context with HealthSathi.
    """

    def __init__(self, chat_ctx: llm.ChatContext | None = None) -> None:
        super().__init__(
            instructions=CLINIC_SATHI_PROMPT,
            chat_ctx=chat_ctx,
            tts=murf.TTS(
                voice="Pooja",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
                text_pacing=True,
            ),
        )

    async def on_enter(self) -> None:
        logger.info("Entering ClinicSathi (voice: Murf Falcon · Pooja)")
        try:
            if (
                hasattr(self, "session")
                and self.session
                and hasattr(self.session, "room_io")
            ):
                room = getattr(self.session.room_io, "room", None)
                if (
                    room
                    and hasattr(room, "local_participant")
                    and room.local_participant
                ):
                    self._attr_task = asyncio.create_task(
                        room.local_participant.set_attributes(
                            {
                                "agent_name": "ClinicSathi",
                                "agent_title": "Healthcare Facility Specialist",
                                "voice_name": "Murf Falcon · Pooja",
                            }
                        )
                    )
        except Exception as e:
            logger.debug(f"Attribute update notice: {e}")

        # Automatically greet the user upon handoff in Pooja's voice
        try:
            if hasattr(self, "session") and self.session:
                async def _greet_on_switch():
                    try:
                        await asyncio.sleep(0.3)
                        await self.session.say(
                            "Hi, I'm ClinicSathi. I'm here to help you find nearby clinics, PHCs, or hospitals, and prepare for your doctor visit. Which city or area are you looking in?",
                            allow_interruptions=True,
                        )
                    except Exception as g_err:
                        logger.debug(f"ClinicSathi handoff greeting notice: {g_err}")

                self._greet_task = asyncio.create_task(_greet_on_switch())
        except Exception as e:
            logger.debug(f"ClinicSathi greeting trigger notice: {e}")

    @function_tool
    async def find_nearby_facility(
        self,
        context: RunContext,
        location: str = "",
        facility_type: str = "any",
        urgency: str = "routine",
    ) -> str:
        """Find an appropriate nearby health facility or hospital based on the user's location.
        Looks up registered hospitals and PHCs in Pune, Nagpur, Mumbai, Delhi, and surrounding areas.

        Parameters:
            location: User's area, city, or district (e.g. 'Pune', 'Nagpur', 'Mumbai', 'Delhi').
            facility_type: Preferred facility type — 'health_post', 'phc', 'clinic', 'hospital', or 'any'.
            urgency: Triage urgency level — 'self_care', 'routine', 'soon', or 'urgent'.
        RESPONSE RULE: You MUST explicitly mention the specific hospital names and city in your spoken response.
        """
        try:
            facility_map = {
                "self_care": {
                    "recommended": "Local Primary Health Centre (PHC) or pharmacy",
                    "tip": "For mild symptoms, your nearest PHC or community pharmacy can help.",
                },
                "routine": {
                    "recommended": "Primary Health Centre (PHC) or General Hospital",
                    "tip": "Visit your local PHC or registered hospital. Bring your health card if you have one.",
                },
                "soon": {
                    "recommended": "District / Specialty Hospital",
                    "tip": (
                        "Please visit a major district or specialty hospital today. "
                        "If possible, call ahead."
                    ),
                },
                "urgent": {
                    "recommended": "Nearest Emergency Department / Tertiary Hospital",
                    "tip": (
                        "Go to the nearest hospital emergency department immediately, or call 112 / 102 for an ambulance. "
                        "Do not wait."
                    ),
                },
            }

            guidance = facility_map.get(urgency, facility_map["routine"])
            loc_clean = location.strip()
            matched_facilities = get_nearby_facilities(loc_clean)

            facility_list = []
            if matched_facilities:
                for f in matched_facilities[:3]:
                    facility_list.append(
                        {
                            "name": f.get("facility_name"),
                            "type": f.get("facility_type"),
                            "address": f.get("address"),
                            "contact": f.get("contact_number"),
                        }
                    )

            location_note = f"In or near {loc_clean}: " if loc_clean else ""

            result = {
                "location_hint": loc_clean or "your area",
                "recommended_facility_type": guidance["recommended"],
                "specific_facilities": facility_list,
                "tip": f"{location_note}{guidance['tip']}",
                "emergency_number": "112 / 102",
                "disclaimer": (
                    "ClinicSathi provides facility information for guidance. "
                    "Please confirm services directly with the facility or call 112 in emergencies."
                ),
            }
            update_current_call_outcome(context, "FACILITY_FOUND", "successful")
            logger.info(
                f"TOOL CALL: find_nearby_facility [ClinicSathi] "
                f"(location='{location}', found={len(facility_list)} matches, urgency='{urgency}')"
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            logger.error(f"TOOL ERROR in find_nearby_facility [ClinicSathi]: {e}")
            update_current_call_outcome(context, "TECHNICAL_ERROR", "failed")
            raise

    @function_tool
    async def search_health_resources(
        self,
        context: RunContext,
        query: str = "",
    ) -> str:
        """Search health information resources for doctor visit preparation or facility guidance."""
        logger.info(
            f"TOOL CALL: search_health_resources [ClinicSathi] (query='{query}')"
        )
        try:
            res = await fn_search_health_resources(context, query=query)
            update_current_call_outcome(context, "GENERAL_GUIDANCE", "successful")
            logger.info("TOOL COMPLETE: search_health_resources [ClinicSathi]")
            return res
        except Exception as e:
            logger.error(f"TOOL ERROR in search_health_resources [ClinicSathi]: {e}")
            update_current_call_outcome(context, "TECHNICAL_ERROR", "failed")
            raise

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        user_confirmed_consent: bool = False,
        reason_type: str = "health_concern",
        issue_summary: str = "User requested human health support",
        urgency: str = "medium",
    ) -> str:
        """Submit a human health support request if needed while in ClinicSathi."""
        logger.info(
            f"TOOL CALL: create_escalation [ClinicSathi] (consent={user_confirmed_consent}, reason='{reason_type}', urgency='{urgency}')"
        )
        try:
            res = await fn_create_escalation(
                context=context,
                user_confirmed_consent=user_confirmed_consent,
                reason_type=reason_type,
                issue_summary=issue_summary,
                urgency=urgency,
            )
            update_current_call_outcome(context, "HUMAN_ESCALATION", "successful")
            logger.info(f"TOOL COMPLETE: create_escalation [ClinicSathi] -> {res}")
            return res
        except Exception as e:
            logger.error(f"TOOL ERROR in create_escalation [ClinicSathi]: {e}")
            update_current_call_outcome(context, "TECHNICAL_ERROR", "failed")
            raise

    @function_tool
    async def transfer_to_health_sathi(
        self,
        context: RunContext,
        reason: str = "general_health_guidance",
    ) -> tuple[Agent, str]:
        """Transfer back to HealthSathi when the user asks general health questions, changes the topic away from facilities/appointments, or the facility task is complete."""
        logger.info(f"TOOL CALL: transfer_to_health_sathi (reason='{reason}')")
        chat_ctx = self.chat_ctx.copy(exclude_instructions=True)
        main_agent = Assistant(chat_ctx=chat_ctx)
        logger.info(
            "TOOL COMPLETE: transfer_to_health_sathi -> switching back to HealthSathi"
        )
        return (
            main_agent,
            "Transferring back to HealthSathi for general health support.",
        )


def _clean_tts_text(text: str) -> str:
    """Sanitize spoken text output to ensure no raw tool tags, XML, JSON, or formatting noise reach TTS audio synthesis."""
    if not text:
        return ""

    # 1. Remove pseudo tool calls like find_nearby_facility>{...} or tool_name>{...}
    text = re.sub(r"\b\w+>\s*\{[^}]*\}?", "", text)
    text = re.sub(
        r"\(?\s*function\s*=\s*\w+[^>)]*[\)>]?", "", text, flags=re.IGNORECASE
    )
    text = re.sub(
        r"</?(?:function|tool_call|tool)[^>]*>", "", text, flags=re.IGNORECASE
    )
    text = re.sub(r"\(?\s*function[\s\S]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    # 2. Remove any JSON structures or raw parameter dictionaries (complete OR unclosed)
    text = re.sub(
        r"\{\s*\"(?:name|parameters|symptoms|duration_days|severity|facility_type|location|urgency|who_needs_help|reason_type|issue_summary|checked_by_agent|preferred_language|preferred_contact|user_id|reference_id|key|value|category|query)\"[\s\S]*?\}",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\{\s*\"[^\"]+\"\s*:[\s\S]*?\}", "", text)
    text = re.sub(r"\{[\s\S]*?\}", "", text)

    # 3. Strip markdown formatting symbols and unwanted characters
    text = re.sub(r"[\/\\\_\|\#\*\=\+\@\%\^\&\~\`]+", " ", text)
    text = re.sub(r"\.{2,}", ".", text)
    return re.sub(r"\s+", " ", text).strip()


server = AgentServer(job_executor_type=JobExecutorType.THREAD)


def prewarm(proc: JobProcess):
    # Responsive noise-resilient VAD tuned to avoid stuck-in-listening states
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=0.25,
        prefix_padding_duration=0.15,
    )
    init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext) -> None:
    # Set up call state tracking for analytics
    import time
    import uuid

    room_name = (
        ctx.room.name
        if ctx.room and ctx.room.name
        else f"healthsathi-room-{uuid.uuid4().hex[:8]}"
    )
    call_state = {
        "session_id": str(uuid.uuid4()),
        "room_name": room_name,
        "start_time": time.time(),
        "channel": "browser",
        "user_spoke": False,
        "outcome": "incomplete",
        "outcome_type": "INCOMPLETE",
    }
    ctx.proc.userdata["call_state"] = call_state

    # Start persistent background daily practice scheduler if not running
    if "sched_task" not in ctx.proc.userdata:
        try:
            from scheduler import start_scheduler_loop

            ctx.proc.userdata["sched_task"] = asyncio.create_task(
                start_scheduler_loop()
            )
        except Exception as sched_err:
            logger.warning(f"Could not start background scheduler: {sched_err}")

    # Logging setup
    ctx.log_context_fields = {
        "room": room_name,
    }

    # LLM Initialization: Multi-provider support (OpenRouter -> NVIDIA -> Groq -> Google Gemini)
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    google_key = os.getenv("GOOGLE_API_KEY", "").strip()

    try:
        if provider == "openrouter" or (not provider and openrouter_key):
            openrouter_model = os.getenv(
                "OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct"
            ).strip()
            logger.info(f"LLM Provider: OpenRouter ({openrouter_model})")
            llm_inst = openai.LLM(
                model=openrouter_model,
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key,
                temperature=0.3,
                parallel_tool_calls=False,
                timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
            )
        elif provider == "nvidia" or (not provider and nvidia_key):
            nvidia_model = os.getenv(
                "NVIDIA_MODEL", "meta/llama-3.1-8b-instruct"
            ).strip()
            nvidia_base_url = os.getenv(
                "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
            ).strip()
            logger.info(f"LLM Provider: NVIDIA API ({nvidia_model})")
            llm_inst = openai.LLM(
                model=nvidia_model,
                base_url=nvidia_base_url,
                api_key=nvidia_key,
                temperature=0.3,
                top_p=1.0,
                parallel_tool_calls=False,
                timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
            )
        elif provider == "groq" or (not provider and groq_key):
            groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
            logger.info(f"LLM Provider: Groq API ({groq_model})")
            llm_inst = openai.LLM(
                model=groq_model,
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key,
                temperature=0.3,
                parallel_tool_calls=False,
                timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
            )
        elif provider == "google" or (not provider and google_key):
            logger.info("LLM Provider: Google Gemini (gemini-2.0-flash)")
            llm_inst = google.LLM(model="gemini-2.0-flash")
        else:
            raise ValueError(
                "No valid LLM API key (OpenRouter, NVIDIA, Groq, or Google) found in environment."
            )
    except Exception as llm_init_err:
        logger.warning(
            f"Failed to initialize primary LLM provider '{provider}': {llm_init_err}. "
            f"Attempting fallback provider..."
        )
        if google_key:
            logger.info("Fallback LLM Provider: Google Gemini (gemini-2.0-flash)")
            llm_inst = google.LLM(model="gemini-2.0-flash")
        elif groq_key:
            logger.info("Fallback LLM Provider: Groq API (llama-3.1-8b-instant)")
            llm_inst = openai.LLM(
                model="llama-3.1-8b-instant",
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key,
                temperature=0.7,
                parallel_tool_calls=False,
            )
        else:
            raise llm_init_err

    # Built-in text transforms to strip markdown and emojis from spoken audio
    tts_transforms = ["filter_markdown", "filter_emoji"]

    # Set up a shared voice AI pipeline matching official Murf multilingual recommendation
    # Default TTS voice is Samar (HealthSathi); specialist agent dynamically switches to Pooja (ClinicSathi)
    session_kwargs = {
        # Speech-to-text (STT) via Deepgram Nova-3 with multilingual support (en + hi + hinglish)
        "stt": deepgram.STT(model="nova-3", language="multi", smart_format=True),
        # Large Language Model (LLM) processing user input and executing function tools
        "llm": llm_inst,
        # Text-to-speech (TTS) via Murf Falcon (min_sentence_len=1 for immediate audio streaming)
        "tts": murf.TTS(
            voice="Samar",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
            text_pacing=True,
        ),
        "vad": ctx.proc.userdata["vad"],
        # Responsive endpointing delays (0.15s silence threshold, 0.5s max phrase window)
        "min_endpointing_delay": 0.15,
        "max_endpointing_delay": 0.5,
        # Preemptive generation for faster turn-taking
        "preemptive_generation": True,
        "tts_text_transforms": tts_transforms,
        "user_away_timeout": 8.0,
        "userdata": {"call_state": call_state},
    }

    session = AgentSession(**session_kwargs)

    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev):
        call_state["user_spoke"] = True
        if call_state.get("outcome") != "successful":
            call_state["outcome"] = "successful"
            if call_state.get("outcome_type") == "INCOMPLETE":
                call_state["outcome_type"] = "GENERAL_GUIDANCE"
        _prune_history(session, max_turns=6)
        logger.info("USER TURN COMMITTED")
        logger.info("LLM GENERATION STARTING...")

    @session.on("agent_state_changed")
    def _on_agent_state_changed(ev):
        new_state = str(getattr(ev, "new_state", getattr(ev, "state", ev))).lower()
        old_state = str(getattr(ev, "old_state", "")).lower()
        if "speaking" in new_state:
            if call_state.get("outcome") != "successful":
                call_state["outcome"] = "successful"
                if call_state.get("outcome_type") == "INCOMPLETE":
                    call_state["outcome_type"] = "GENERAL_GUIDANCE"
            logger.info("LLM GENERATION COMPLETE -> MURF TTS STARTING...")
        elif "speaking" in old_state and "listening" in new_state:
            logger.info("MURF TTS AUDIO PLAYBACK COMPLETE")

    @session.on("user_state_changed")
    def _on_user_state_changed(ev):
        new_state = getattr(ev, "new_state", "")
        if new_state == "away":
            logger.info(
                "USER SILENT (8s timeout) -> Auto-generating conversation continuation prompt"
            )
            session.generate_reply(
                instructions="The user has been quiet for a few seconds. Gently check in and ask how you can help with their health concern."
            )

    # Attach event listener for TPM rate-limit exception handling
    @session.on("error")
    def _on_session_error(err):
        err_str = str(err).lower()
        if "429" in err_str or "tpm" in err_str or "rate limit" in err_str:
            logger.error(f"LLM API rate limit error detected: {err}")

            async def _speak_error():
                try:
                    await session.say(
                        "I'm a little busy right now. Give me a few seconds and try again.",
                        allow_interruptions=True,
                    )
                except Exception as say_err:
                    logger.warning(f"Error speaking rate limit message: {say_err}")

            err_task = asyncio.create_task(_speak_error())
            ctx.proc.userdata["err_task"] = err_task

    # Join the room and connect to the user first
    await ctx.connect()

    # Start the session with HealthSathi (Assistant) as default active agent
    session_started = asyncio.create_task(
        session.start(
            agent=Assistant(),
            room=ctx.room,
        )
    )
    ctx.proc.userdata["session_task"] = session_started

    # Track user interaction and deliver initial personalized voice greeting
    try:
        participant = await asyncio.wait_for(ctx.wait_for_participant(), timeout=5.0)
        user_id = (
            participant.identity
            if participant and participant.identity
            else "default_user"
        )
        user_data = get_or_create_user(user_id=user_id)
        ctx.proc.userdata["user_id"] = user_id

        # Launch non-blocking background task to pre-fetch memory cache
        prefetch_task = asyncio.create_task(async_prefetch_user_memory(user_id))
        ctx.proc.userdata["prefetch_task"] = prefetch_task

        # Check if room or participant represents an outbound call session
        is_outbound = False
        if (
            ctx.room
            and ctx.room.name
            and ("outbound" in ctx.room.name.lower() or "sip" in ctx.room.name.lower())
        ):
            is_outbound = True
        if (
            participant
            and getattr(participant, "attributes", None)
            and participant.attributes.get("is_outbound") == "true"
        ):
            is_outbound = True

        if is_outbound:
            call_state["channel"] = "SIP"

        name = user_data.get("name") if user_data else None

        if is_outbound:
            if name:
                greeting_text = f"Hi {name}, this is HealthSathi, your health support companion. I'm calling for your scheduled health reminder. Is this a good time to talk? You can say stop at any time to end the call."
            else:
                greeting_text = "Hi, this is HealthSathi, your health support companion. I'm calling for your scheduled health reminder. Is this a good time to talk? You can say stop at any time to end the call."
        elif name:
            greeting_text = f"Welcome back {name}! How are you feeling today?"
        else:
            greeting_text = "Hi, I'm HealthSathi, your friendly voice companion for everyday health guidance. How can I help you today?"

        async def _deliver_greeting():
            try:
                await asyncio.sleep(0.3)
                await session.say(
                    _clean_tts_text(greeting_text), allow_interruptions=True
                )
                if call_state.get("outcome") != "successful":
                    call_state["outcome"] = "successful"
                    if call_state.get("outcome_type") == "INCOMPLETE":
                        call_state["outcome_type"] = "GENERAL_GUIDANCE"
            except (Exception, asyncio.CancelledError) as e:
                logger.info(f"Initial greeting delivery ended or cancelled: {e}")

        greeting_task = asyncio.create_task(_deliver_greeting())
        ctx.proc.userdata["greeting_task"] = greeting_task
    except (Exception, asyncio.CancelledError) as err:
        logger.info(f"Participant greeting setup skipped: {err}")

    # Keep agent entrypoint active until session completes, then save final call analytics
    try:
        await session_started
    finally:
        duration = max(
            1, int(time.time() - call_state.get("start_time", time.time()))
        )
        if (call_state.get("user_spoke") or duration > 3) and call_state.get(
            "outcome"
        ) != "successful":
            call_state["outcome"] = "successful"
            if call_state.get("outcome_type") == "INCOMPLETE":
                call_state["outcome_type"] = "GENERAL_GUIDANCE"
        try:
            save_call_analytics(
                session_id=call_state["session_id"],
                duration=duration,
                channel=call_state["channel"],
                outcome=call_state["outcome"],
                outcome_type=call_state["outcome_type"],
            )
            logger.info(
                f"RECORDED CALL ANALYTICS: session_id='{call_state['session_id']}', "
                f"duration={duration}s, channel='{call_state['channel']}', "
                f"outcome='{call_state['outcome']}', outcome_type='{call_state['outcome_type']}'"
            )
        except Exception as save_err:
            logger.error(f"Error saving call analytics on disconnect: {save_err}")


if __name__ == "__main__":
    cli.run_app(server)
