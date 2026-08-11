"""
Scoring module for the BolBuddy Voice Agent.

Provides a lightweight heuristic evaluator for spoken English answers.
No external API calls — pure Python analysis for zero-latency, zero-cost scoring.
"""

import json
import logging
import re

from livekit.agents import RunContext, function_tool

logger = logging.getLogger("agent.scoring")

# Common filler words that reduce clarity
_FILLERS = {"um", "uh", "like", "you know", "basically", "actually", "literally"}

# Basic grammar error patterns (simple heuristic, not exhaustive)
_GRAMMAR_ISSUES = [
    (r"\bi\b(?!\s*')", "Capitalize 'I'"),
    (r"\b(he|she|it)\s+(have|go|do|make|come)\b", "subject-verb agreement"),
    (r"\b(i|we|they|you)\s+(has|goes|does|makes|comes)\b", "subject-verb agreement"),
    (r"\b(is|are|was|were)\s+(go|come|do|make)\b", "auxiliary + base form"),
]


def _count_fillers(text: str) -> int:
    """Count filler words in transcript."""
    lower = text.lower()
    return sum(lower.count(f) for f in _FILLERS)


def _check_grammar(text: str) -> list[str]:
    """Return list of brief grammar issue descriptions found."""
    issues = []
    lower = text.lower()
    for pattern, desc in _GRAMMAR_ISSUES:
        if re.search(pattern, lower):
            issues.append(desc)
    return issues[:2]  # Cap at 2 to keep output small


def _assess_vocabulary(text: str) -> str:
    """Quick vocabulary richness check."""
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    if not words:
        return "limited"
    unique_ratio = len(set(words)) / len(words)
    if unique_ratio > 0.75:
        return "varied"
    elif unique_ratio > 0.5:
        return "adequate"
    return "repetitive"


def _compute_score(
    transcript: str,
) -> dict[str, object]:
    """
    Compute a 1-10 score with strength, improvement, and example.

    Evaluates: clarity, basic grammar, vocabulary, naturalness.
    Does not penalize Indian English patterns.
    """
    if not transcript or not transcript.strip():
        return {"error": "No transcript provided."}

    text = transcript.strip()
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    word_count = len(words)

    if word_count < 2:
        return {"error": "Transcript too short to evaluate."}

    # Start at 7 (assume decent effort) and adjust
    score = 7.0

    # --- Clarity ---
    filler_count = _count_fillers(text)
    filler_ratio = filler_count / max(word_count, 1)
    if filler_ratio > 0.15:
        score -= 1.5
    elif filler_ratio > 0.05:
        score -= 0.5

    # Sentence structure: at least one complete sentence
    sentences = re.split(r"[.!?]+", text)
    real_sentences = [s.strip() for s in sentences if len(s.strip().split()) >= 3]
    if len(real_sentences) >= 2:
        score += 0.5
    elif len(real_sentences) == 0:
        score -= 1.0

    # --- Grammar ---
    grammar_issues = _check_grammar(text)
    score -= len(grammar_issues) * 0.5

    # --- Vocabulary ---
    vocab = _assess_vocabulary(text)
    if vocab == "varied":
        score += 0.5
    elif vocab == "repetitive":
        score -= 0.5

    # --- Naturalness ---
    # Bonus for conversational connectors
    connectors = {"so", "because", "and", "but", "also", "then", "however"}
    connector_count = sum(1 for w in words if w.lower() in connectors)
    if connector_count >= 2:
        score += 0.5

    # Clamp to 1-10
    score = max(1, min(10, round(score)))

    # Determine strength and improvement
    if filler_ratio <= 0.05 and not grammar_issues:
        strength = "clear ideas"
    elif not grammar_issues:
        strength = "good structure"
    elif filler_ratio <= 0.05:
        strength = "clear delivery"
    else:
        strength = "willing to communicate"

    if grammar_issues:
        improvement = grammar_issues[0]
    elif filler_ratio > 0.05:
        improvement = "reduce filler words"
    elif vocab == "repetitive":
        improvement = "use more varied vocabulary"
    elif len(real_sentences) < 2:
        improvement = "try forming complete sentences"
    else:
        improvement = "make phrasing more natural"

    # Generate a brief corrected example from the transcript
    example = _generate_example(text, grammar_issues, filler_count)

    return {
        "score": int(score),
        "strength": strength,
        "improvement": improvement,
        "example": example,
    }


def _generate_example(text: str, grammar_issues: list[str], filler_count: int) -> str:
    """Generate a short corrected example phrase from the transcript."""
    # Take the first sentence as base
    sentences = re.split(r"[.!?]+", text)
    base = sentences[0].strip() if sentences else text.strip()

    # Limit to first ~12 words
    words = base.split()
    if len(words) > 12:
        base = " ".join(words[:12]) + "."

    # Remove obvious fillers
    for filler in _FILLERS:
        base = re.sub(r"\b" + re.escape(filler) + r"\b", "", base, flags=re.IGNORECASE)

    # Clean up extra spaces
    base = re.sub(r"\s+", " ", base).strip()

    # Capitalize first letter
    if base:
        base = base[0].upper() + base[1:]

    # Ensure it ends with punctuation
    if base and base[-1] not in ".!?":
        base += "."

    return base


@function_tool
async def score_spoken_answer(
    context: RunContext,
    question: str = "",
    answer: str = "",
    transcript: str = "",
    practice_topic: str = "",
) -> str:
    """Evaluate a completed spoken English answer. Use only when learner asks for evaluation."""
    try:
        text_to_eval = answer or transcript
        result = _compute_score(text_to_eval)
        if "error" in result:
            logger.info(f"TOOL score_spoken_answer: failure ({result['error']})")
            return json.dumps({"error": "Could not score that answer right now."})

        logger.info(f"TOOL score_spoken_answer: success (score={result['score']})")
        return json.dumps(result)
    except Exception as e:
        logger.error(f"TOOL score_spoken_answer: failure ({e})")
        return json.dumps({"error": "Could not score that answer right now."})
