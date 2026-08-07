# README_PROMPT_ARCHITECTURE.md

## Prompt Architecture

BolBuddy's system prompt is intentionally divided into small, focused modules rather than one large prompt.

Each module has a single responsibility.

This makes the prompt easier to understand, maintain, test, and extend as new capabilities are added throughout the Voice for Bharat challenge.

The complete system prompt is assembled inside `system_prompt.py`.

---

## Prompt Modules

### identity.py

Defines who BolBuddy is, who it serves, its purpose, personality, and long-term mission.

Whenever the identity or purpose of the assistant changes, update this module.

---

### objectives.py

Defines what successful conversations should achieve.

Focuses on conversation goals rather than implementation.

Update this module whenever new learning objectives or success criteria are introduced.

---

### knowledge.py

Defines what BolBuddy knows, where its expertise begins, and where it ends.

It establishes the assistant's domain knowledge while preventing it from acting outside its intended role.

---

### language.py

Defines how BolBuddy communicates.

Includes multilingual behavior, code-mixed conversations, language adaptation, voice-first communication, and conversational tone.

Future multilingual improvements should belong here.

---

### guardrails.py

Defines safety boundaries.

Specifies what BolBuddy must refuse, what it must never claim, ethical behavior, learner protection, escalation behavior, and domain limitations.

All future safety-related rules belong here.

---

### style.py

Defines BolBuddy's conversational personality.

Includes pacing, sentence length, correction style, emotional intelligence, encouragement strategy, and overall speaking style.

Future personality refinements should be made here.

---

### greeting.py

Defines the first interaction with the learner.

Contains welcome messages and first-turn behavior.

---

### conversation_principles.py

Contains timeless conversational principles that guide every interaction.

These principles remain stable even as new features are added.

They define how BolBuddy approaches conversations rather than specific functionality.

---

### decision_hierarchy.py

Defines the priority order BolBuddy should follow whenever multiple instructions or behaviors could apply.

Acts as the assistant's internal decision-making framework.

---

## Design Principles

The architecture follows several core principles:

* One responsibility per module.
* Favor clarity over complexity.
* Keep prompts modular and reusable.
* Voice-first design before text-first design.
* Conversation before instruction.
* Confidence before perfection.
* Practice before explanation.
* Safety before capability.

---

## Future Expansion

As BolBuddy evolves, new capabilities should be added by extending existing modules whenever appropriate.

Examples include:

* Memory
* Personalization
* Pronunciation feedback
* Progress tracking
* Vocabulary reinforcement
* Conversation history
* Adaptive difficulty
* Role-play scenarios
* Tool usage
* External knowledge
* Retrieval systems

Avoid creating large monolithic prompts.

Instead, preserve modularity by expanding the most relevant prompt module or creating a new focused module only when a completely new responsibility is introduced.

---

## Philosophy

BolBuddy is not designed to be an English teacher.

It is designed to be an AI speaking companion.

Every design decision should support one central mission:

**Help learners become confident English speakers through natural conversations—not lessons.**
