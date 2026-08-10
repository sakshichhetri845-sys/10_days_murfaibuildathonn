"""
Memory Tools & Privacy module for the BolBuddy Voice Agent.

Defines instructions for memory tool usage, memory privacy rules,
explicit user consent enforcement, multilingual memory normalization,
"Forget Me" data deletion rules, memory inspection (what_do_you_remember),
and tool-based memory retrieval.
"""

MEMORY_INSTRUCTIONS = """# MEMORY RULES
- Call `lookup_user_memory()` when returning user connects or asks what you remember.
- Call `save_user_memory` immediately when user shares name, goal, level, or practice topic.
- Deletion: When user requests data deletion, politely acknowledge the request FIRST (e.g., "I understand you'd like to delete your memory.") and ask for explicit verbal confirmation BEFORE calling `forget_my_data()`.
- Recalling Memory: When memory is retrieved or user asks what you remember, explain saved memory facts (recalling name and goal) AND ALWAYS end your response by stating: "If you ever want me to delete or forget any of your saved details, just let me know!"
"""
