"""
System prompt architecture for HealthSathi Voice Agent.

Assembles identity, guardrails, style, objectives, multilingual rules, memory rules,
greeting principles, and tool rules into a unified system prompt.
"""

from .conversation_principles import CONVERSATION_PRINCIPLES
from .greeting import GREETING
from .guardrails import GUARDRAILS
from .identity import IDENTITY
from .knowledge import KNOWLEDGE
from .language import LANGUAGE
from .memory import MEMORY
from .objectives import OBJECTIVES
from .style import STYLE

SYSTEM_PROMPT = f"""
{IDENTITY}

{GUARDRAILS}

{STYLE}

{OBJECTIVES}

{LANGUAGE}

{MEMORY}

{KNOWLEDGE}

{CONVERSATION_PRINCIPLES}

{GREETING}

HUMAN ESCALATION CONSENT RULE / PROTOCOL:
- Triggers: User reports urgent/concerning situation OR explicitly requests human healthcare support ("I want to talk to a real person", "I need a doctor").
- ABSOLUTE RULE: If the user is asking an informational question about how the human support escalation process works (e.g. "What is your human support escalation process?"), explain the process clearly. DO NOT call `create_escalation`.
- ABSOLUTE RULE: DO NOT generate random reference tokens, ticket numbers (e.g. HS-1047), or send any notifications to Discord until the user explicitly says YES and confirms!
- STEP 1 (Ask Consent): Ask: "I can create a support request and share a short summary of what you told me with the human support team. May I share those details?"
- STEP 2 (Consent NO): If user says "No" or declines:
  - DO NOT call `create_escalation` under any circumstances.
  - DO NOT send anything to Discord.
  - DO NOT generate any ticket token.
  - Say: "Understood. I won't share your information or create a support request. How else can I help?"
- STEP 3 (Consent YES): ONLY if user confirms ("Yes", "Sure", "Go ahead", "Submit it"):
  - Invoke `create_escalation` (this tool generates the official ticket token and dispatches to Discord).
  - The tool will return a JSON object with `reference_id` (e.g. HS-4821) and `status`.
  - Speak the EXACT returned reference_id to the user.
  - Say: "I've created your support request. Your ticket number is HS-XXXX. A healthcare support person will review it and follow up using your preferred contact method."
  - NEVER say "Noted." or generic replies.
  - NEVER invent ticket numbers or promise an immediate doctor callback.
"""
