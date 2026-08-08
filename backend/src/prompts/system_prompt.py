"""
System Prompt module for the HealthSaathi Voice Agent.

This module houses the system prompt and its components in a clean,
modular structure. Prompt sections (Identity, Objectives, Knowledge, Language,
Guardrails, Style, Greeting, Conversation Principles, etc.) are imported as modular constants and composed
into `SYSTEM_PROMPT`.
"""

from .conversation_principles import CONVERSATION_PRINCIPLES
from .greeting import GREETING
from .guardrails import GUARDRAILS
from .identity import IDENTITY
from .knowledge import KNOWLEDGE
from .language import LANGUAGE
from .objectives import OBJECTIVES
from .style import STYLE

# Complete system prompt composed from modular sections in exact priority sequence
SYSTEM_PROMPT = f"{IDENTITY}\n\n{GUARDRAILS}\n\n{OBJECTIVES}\n\n{KNOWLEDGE}\n\n{LANGUAGE}\n\n{STYLE}\n\n{GREETING}\n\n{CONVERSATION_PRINCIPLES}"
