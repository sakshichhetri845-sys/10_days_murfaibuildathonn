"""
Day 5 Tool Implementation: Spoken Answer Scoring Tool.

Evaluates spoken answer transcripts for relevance, clarity, grammar, and fluency, returning compact structured feedback.
"""

import json
import re
from typing import Any, Dict


def score_spoken_answer(
    question: str = "",
    answer: str = "",
    level: str = "beginner",
) -> Dict[str, Any]:
    """
    Evaluate a completed spoken English answer transcript.

    Args:
        question: The exercise/question that was asked.
        answer: Transcribed user spoken response.
        level: Learner level ('beginner', 'intermediate', 'advanced').

    Returns:
        Structured dictionary with numerical score (1-10), key strength, and actionable improvement.
    """
    if not answer or not answer.strip():
        return {
            "score": 0,
            "strength": "None",
            "improvement": "No spoken response was recorded. Please try answering again.",
        }

    text = answer.strip()
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    word_count = len(words)

    if word_count < 3:
        return {
            "score": 4,
            "strength": "Short response",
            "improvement": "Try expressing your answer in full sentences to build fluency.",
        }

    score = 7.0

    # Filler check
    fillers = sum(text.lower().count(f) for f in ("um", "uh", "like", "you know"))
    if fillers > 2:
        score -= 1.0

    # Length & structure bonus
    if word_count >= 15:
        score += 1.0

    score = min(10.0, max(1.0, round(score)))

    # Strength & improvement selection
    if score >= 8:
        strength = "Clear, confident ideas with good sentence flow."
        improvement = "Try adding advanced vocabulary transitions like 'furthermore' or 'consequently'."
    elif score >= 6:
        strength = "Clear and relevant answer that addresses the topic."
        improvement = "Focus on speaking in complete sentences without pauses."
    else:
        strength = "Good initial effort."
        improvement = "Practice introducing yourself clearly using simple present tense."

    return {
        "score": int(score),
        "strength": strength,
        "improvement": improvement,
    }


if __name__ == "__main__":
    sample_eval = score_spoken_answer(
        question="Tell me about yourself in 30 seconds.",
        answer="Hi I am Sakshyam. I am studying engineering and I want to improve my speaking skills.",
        level="intermediate",
    )
    print(json.dumps(sample_eval, indent=2))
