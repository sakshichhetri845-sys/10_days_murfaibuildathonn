"""
Locally curated English speaking exercises dataset for BolBuddy.

Provides curated speaking practice questions for Indian students covering:
- Job & Internship Interviews (self introduction, motivation, strengths, career goals, project experience)
- College & Viva (project explanation, technical concepts, experiments)
- Campus Presentations (openings, explaining ideas, project presentations, conclusions)
- Everyday English (introductions, hobbies, routines, college life)

Designed around common student learning contexts with beginner, intermediate, and advanced levels.
"""

import logging
from typing import Any

logger = logging.getLogger("agent.exercises")

EXERCISES_DATASET: dict[str, dict[str, dict[str, str]]] = {
    "interview": {
        "self introduction": {
            "beginner": "Tell me about yourself in 30 seconds.",
            "intermediate": "Give a concise 1-minute professional introduction highlighting your background.",
            "advanced": "Deliver a compelling pitch introducing your professional profile and core interests.",
        },
        "internship motivation": {
            "beginner": "Why are you interested in applying for this internship?",
            "intermediate": "What specific skills do you hope to develop during this internship?",
            "advanced": "How does this internship align with your long-term career aspirations?",
        },
        "strengths": {
            "beginner": "What is one of your greatest strengths?",
            "intermediate": "Describe a key strength of yours with a real-life example.",
            "advanced": "How do your key strengths enable you to overcome challenges in a team?",
        },
        "career goals": {
            "beginner": "Where do you see yourself in the next two years?",
            "intermediate": "What career goals are you working towards right now?",
            "advanced": "Describe your ideal professional growth trajectory over the next 3 to 5 years.",
        },
        "project experience": {
            "beginner": "Tell me briefly about a project you worked on.",
            "intermediate": "Explain a recent project and your individual contribution to it.",
            "advanced": "Describe a complex technical project, the problem solved, and key outcomes.",
        },
    },
    "viva": {
        "explain a project": {
            "beginner": "Explain your final year or class project in simple words.",
            "intermediate": "Summarize the objectives, methodology, and results of your main project.",
            "advanced": "Defend the technical design choices made in your project during viva Q&A.",
        },
        "explain a technical concept": {
            "beginner": "Explain a core concept from your favorite subject to a beginner.",
            "intermediate": "Define a key technical concept and explain how it operates in real applications.",
            "advanced": "Compare two competing technical concepts and highlight their trade-offs.",
        },
        "describe an experiment": {
            "beginner": "Describe a lab experiment you conducted recently.",
            "intermediate": "Explain the step-by-step procedure and safety measures of a lab experiment.",
            "advanced": "Analyze potential error sources and results analysis of a scientific experiment.",
        },
    },
    "presentation": {
        "opening a presentation": {
            "beginner": "How would you start a talk to welcome your audience?",
            "intermediate": "Deliver an engaging 2-sentence hook and introduction for a presentation topic.",
            "advanced": "Open a keynote presentation with a compelling story, hook, and agenda overview.",
        },
        "explaining an idea": {
            "beginner": "Share one idea you have for improving campus student life.",
            "intermediate": "Present a clear proposal explaining an idea and why it matters.",
            "advanced": "Structure a persuasive pitch detailing the problem, proposed solution, and benefits.",
        },
        "presenting a project": {
            "beginner": "Present the main topic of your project in two sentences.",
            "intermediate": "Walk the audience through your project workflow and key findings.",
            "advanced": "Deliver a dynamic slide demonstration summarizing project impact and metrics.",
        },
        "concluding a presentation": {
            "beginner": "How do you thank the audience and end your presentation?",
            "intermediate": "Summarize your 3 main takeaways and invite audience questions.",
            "advanced": "Conclude a presentation with a strong call-to-action and Q&A session opening.",
        },
    },
    "everyday": {
        "introduce yourself": {
            "beginner": "Introduce yourself warmly to a new friend in English.",
            "intermediate": "Introduce yourself, your hometown, and what you enjoy doing.",
            "advanced": "Engage in a friendly social introduction sharing your story and interests.",
        },
        "hobbies": {
            "beginner": "What do you like to do in your free time?",
            "intermediate": "Talk about a hobby you are passionate about and why you enjoy it.",
            "advanced": "Describe how your favorite hobby helps you relax and build personal skills.",
        },
        "daily routine": {
            "beginner": "What is your daily morning routine?",
            "intermediate": "Describe how you plan and manage your typical college day.",
            "advanced": "Reflect on how you balance studies, personal health, and hobbies daily.",
        },
        "college life": {
            "beginner": "What do you enjoy most about your college or campus?",
            "intermediate": "Tell a short story about an exciting event or day at college.",
            "advanced": "Discuss how college life has shaped your confidence and perspective.",
        },
    },
}


_CATEGORY_INDICES: dict[str, int] = {}


def _normalize_key(text: str) -> str:
    """Normalize input string to lowercase alphanumeric."""
    return "".join(c for c in text.lower() if c.isalnum() or c.isspace()).strip()


def get_next_exercise(
    level: str = "beginner",
    topic: str = "interview",
) -> dict[str, Any]:
    """
    Retrieve one speaking exercise matching topic and level from local dataset.

    Returns:
        dict with "question" and "skill", or {"error": "..."} on failure.
    """
    clean_level = _normalize_key(level)
    clean_topic = _normalize_key(topic)

    if clean_level not in ("beginner", "intermediate", "advanced"):
        clean_level = "beginner"

    # Category matching
    category_key = None
    if any(k in clean_topic for k in ("interview", "job", "internship", "career")):
        category_key = "interview"
    elif any(k in clean_topic for k in ("viva", "college", "academic", "experiment")):
        category_key = "viva"
    elif any(k in clean_topic for k in ("presentation", "talk", "speech", "idea")):
        category_key = "presentation"
    elif any(k in clean_topic for k in ("everyday", "daily", "hobby", "social")):
        category_key = "everyday"
    else:
        category_key = "interview"  # Default fallback

    subtopics = EXERCISES_DATASET.get(category_key, {})
    if not subtopics:
        return {"error": "Could not load practice question."}

    # Find matching subtopic or default to next rotated subtopic in category
    matched_skill = None
    matched_dict = None

    for skill, level_map in subtopics.items():
        if skill in clean_topic or (len(clean_topic) > 3 and clean_topic in skill):
            matched_skill = skill
            matched_dict = level_map
            break

    if not matched_dict:
        items = list(subtopics.items())
        idx = _CATEGORY_INDICES.get(category_key, 0)
        matched_skill, matched_dict = items[idx % len(items)]
        _CATEGORY_INDICES[category_key] = idx + 1

    question = matched_dict.get(clean_level) or matched_dict.get("beginner")

    if not question:
        return {"error": "Could not load practice question."}

    return {
        "question": question,
        "skill": matched_skill,
    }

