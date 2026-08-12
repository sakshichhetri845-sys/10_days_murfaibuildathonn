"""
Lightweight RAG (Retrieval-Augmented Generation) module for HealthSathi Voice Agent.

Provides zero-dependency document retrieval over health guidance materials in backend/knowledge/.
"""

import os
import re
from typing import Any, Optional

from livekit.agents import RunContext, function_tool

_KNOWLEDGE_DIR_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge"
)

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "so",
    "the",
    "to",
    "what",
    "with",
    "you",
}


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text into lowercase word tokens."""
    return re.findall(r"\w+", text.lower())


def _load_knowledge_docs(
    knowledge_dir: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Load all markdown documents from knowledge directory."""
    target_dir = knowledge_dir or _KNOWLEDGE_DIR_DEFAULT
    docs = []

    if not os.path.exists(target_dir):
        return docs

    for filename in os.listdir(target_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(target_dir, filename)
            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                docs.append(
                    {
                        "filename": filename,
                        "title": filename.replace(".md", "").replace("_", " ").title(),
                        "content": content,
                    }
                )
            except Exception:
                pass

    return docs


def query_health_resources(
    query: str, knowledge_dir: Optional[str] = None, threshold: float = 1.0
) -> Optional[dict[str, Any]]:
    """
    Search health guidance documents using term weighting and title alignment.

    Returns the top matching document dict if similarity >= threshold, else None.
    """
    if not query or not query.strip():
        return None

    query_tokens = [t for t in _tokenize(query) if len(t) > 1]
    if not query_tokens:
        return None

    docs = _load_knowledge_docs(knowledge_dir=knowledge_dir)
    if not docs:
        return None

    meaningful_query_tokens = [t for t in query_tokens if t not in _STOP_WORDS]
    if not meaningful_query_tokens:
        meaningful_query_tokens = query_tokens

    best_doc = None
    best_score = 0.0

    for doc in docs:
        doc_content_lower = doc["content"].lower()
        title_lower = doc["title"].lower()

        score = 0.0
        for token in meaningful_query_tokens:
            if token in title_lower:
                score += 3.0
            elif token in doc_content_lower:
                count = doc_content_lower.count(token)
                score += min(count, 5) * 0.5

        if score > best_score:
            best_score = score
            best_doc = doc

    if best_doc and best_score >= threshold:
        return {
            "title": best_doc["title"],
            "filename": best_doc["filename"],
            "content": best_doc["content"],
            "score": best_score,
        }

    return None


def query_learning_resources(
    query: str, knowledge_dir: Optional[str] = None, threshold: float = 1.0
) -> Optional[dict[str, Any]]:
    """Backward compatible alias for query_health_resources."""
    return query_health_resources(query, knowledge_dir=knowledge_dir, threshold=threshold)


@function_tool
async def search_health_resources(
    context: RunContext,
    query: str,
) -> str:
    """Search health information resources for symptom guidance, doctor visit prep, or general wellness advice."""
    match = query_health_resources(query)
    if not match:
        return "No relevant health guidance document found."

    return f"Information from {match['title']}:\n{match['content'][:600]}"


