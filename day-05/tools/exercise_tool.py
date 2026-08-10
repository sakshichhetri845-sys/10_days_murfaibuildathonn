"""
Day 5 Tool Implementation: Exercise Retrieval Tool.

Fetches structured speaking exercises based on learner level and topic from the curated local dataset.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("day05.exercise_tool")

_DATA_PATH = Path(__file__).parent / "exercise_data.json"


def load_exercise_dataset() -> Dict[str, Any]:
    """Load curated exercise dataset from JSON."""
    if _DATA_PATH.exists():
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def fetch_next_exercise(level: str = "beginner", topic: str = "internship interviews") -> Dict[str, str]:
    """
    Fetch a single practice exercise for a given level and topic.

    Args:
        level: 'beginner', 'intermediate', or 'advanced'
        topic: Practice topic category (e.g., 'internship interviews', 'self introduction')

    Returns:
        Compact JSON-serializable dictionary with exercise text and minimal metadata.
    """
    dataset = load_exercise_dataset().get("topics", {})
    norm_level = level.lower().strip() if level else "beginner"
    norm_topic = topic.lower().strip() if topic else "internship interviews"

    # Match topic or default to internship interviews
    topic_data = dataset.get(norm_topic)
    if not topic_data:
        # Fallback partial match
        for k, v in dataset.items():
            if norm_topic in k or k in norm_topic:
                topic_data = v
                norm_topic = k
                break
    if not topic_data:
        topic_data = dataset.get("internship interviews", {})
        norm_topic = "internship interviews"

    # Match level or default to beginner
    exercise_text = topic_data.get(norm_level)
    if not exercise_text:
        exercise_text = topic_data.get("beginner", "Tell me about yourself in 30 seconds.")

    return {
        "id": f"{norm_topic.replace(' ', '_')}_{norm_level}",
        "level": norm_level,
        "topic": norm_topic,
        "exercise": exercise_text,
    }


if __name__ == "__main__":
    result = fetch_next_exercise("intermediate", "internship interviews")
    print(json.dumps(result, indent=2))
