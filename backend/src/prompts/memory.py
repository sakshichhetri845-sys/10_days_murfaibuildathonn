"""
Memory Tools & Privacy module for the BolBuddy Voice Agent.

Defines instructions for memory tool usage, memory privacy rules,
explicit user consent enforcement, multilingual memory normalization,
"Forget Me" data deletion rules, memory inspection (what_do_you_remember),
and tool-based memory retrieval.
"""

MEMORY_INSTRUCTIONS = """# MEMORY & PRIVACY RULES
- **Lookup**: Call `lookup_user_memory()` whenever a returning user greets, connects, or asks what you remember.
- **Auto Save**: Call `save_user_memory` immediately when the user shares their name, learning goal, or topic.
- **Deletion/Reset**: When user asks to delete/forget/reset/clear memory, ask for explicit verbal confirmation before calling `forget_my_data()`. Once confirmed, immediately call `forget_my_data()`.
- **Recall**: When memory is retrieved or asked about, warmly recall facts AND ALWAYS end with: "If you would ever like me to delete or forget any of your saved memory, just let me know!"
- **Store**: Store facts in clean English (e.g. `name="Rahul"`, `learning_goal="job interview"`).
"""
