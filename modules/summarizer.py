"""
modules/summarizer.py – Summarize, key points, flashcards, quiz generation.

Uses Ollama LLM when available, falls back to mock data.
"""
import json
import logging
from typing import Optional

from modules.llm import generate, generate_json
from modules.prompts import (
    SUMMARY_SYSTEM, SUMMARY_SHORT, SUMMARY_DETAILED, SUMMARY_EXAM,
    KEY_POINTS, FLASHCARDS, QUIZ, MAP_REDUCE_COMBINE,
)
from config import CHUNK_SIZE

logger = logging.getLogger(__name__)

# ── Style mapping ─────────────────────────────────────────────────────────

_STYLE_PROMPTS = {
    "concise": SUMMARY_SHORT,
    "detailed": SUMMARY_DETAILED,
    "exam": SUMMARY_EXAM,
}


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Split text into word-based chunks for map-reduce summarization."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


# ── Public API ────────────────────────────────────────────────────────────

def summarize(text: str, style: str = "concise") -> str:
    """Summarize text using the specified style.
    style: 'concise', 'detailed', or 'exam'."""
    if not text or not text.strip():
        return ""

    prompt_tpl = _STYLE_PROMPTS.get(style, SUMMARY_SHORT)
    chunks = _chunk_text(text)

    if len(chunks) == 1:
        prompt = prompt_tpl.format(text=text)
        return generate(prompt, system=SUMMARY_SYSTEM)

    # Map-reduce for long texts
    chunk_summaries = []
    for chunk in chunks:
        prompt = SUMMARY_SHORT.format(text=chunk)
        chunk_summary = generate(prompt, system=SUMMARY_SYSTEM)
        chunk_summaries.append(chunk_summary)

    combined = "\n\n".join(chunk_summaries)
    final_prompt = MAP_REDUCE_COMBINE.format(summaries=combined)
    return generate(final_prompt, system=SUMMARY_SYSTEM)


def key_points(text: str) -> list[str]:
    """Extract key points as a list of strings."""
    if not text or not text.strip():
        return []

    prompt = KEY_POINTS.format(text=text[:5000])  # limit input
    result = generate_json(prompt, system=SUMMARY_SYSTEM)

    if isinstance(result, list):
        return [str(p) for p in result]

    # Fallback: try to parse as list of strings
    raw = generate(prompt, system=SUMMARY_SYSTEM)
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(p) for p in parsed]
    except (json.JSONDecodeError, TypeError):
        pass

    # Last resort: split by newlines
    return [line.strip("- •").strip() for line in raw.split("\n") if line.strip()]


def generate_flashcards(text: str, n: int = 5) -> list[dict]:
    """Generate n flashcards as [{q, a}, ...]."""
    if not text or not text.strip():
        return []

    prompt = FLASHCARDS.format(text=text[:5000], n=n)
    result = generate_json(prompt, system=SUMMARY_SYSTEM)

    if isinstance(result, list) and all(isinstance(c, dict) for c in result):
        return result[:n]

    return _mock_flashcards()


def generate_quiz(text: str, n: int = 5) -> list[dict]:
    """Generate n MCQ questions as [{question, options, answer_index, explanation}, ...]."""
    if not text or not text.strip():
        return []

    prompt = QUIZ.format(text=text[:5000], n=n)
    result = generate_json(prompt, system=SUMMARY_SYSTEM)

    if isinstance(result, list) and all(isinstance(q, dict) for q in result):
        # Normalize answer format
        for q in result:
            if "answer_index" not in q and "answer" in q:
                ans = q["answer"]
                if isinstance(ans, int):
                    q["answer_index"] = ans
                elif isinstance(ans, str) and ans in q.get("options", []):
                    q["answer_index"] = q["options"].index(ans)
                else:
                    q["answer_index"] = 0
        return result[:n]

    return _mock_quiz()


# ── Mock data (used by core/summarizer.py compatibility layer too) ────────

def mock_summarize_result(text: str = "", style: str = "concise") -> dict:
    """Return a complete mock result shape for UI development."""
    wc = len(text.split()) if text else 2400
    summary_text = (
        "Database normalization is a systematic approach to organizing relational databases "
        "to reduce data redundancy and improve data integrity. The process involves decomposing "
        "tables into smaller, well-structured relations through a series of normal forms (1NF through BCNF). "
        "First Normal Form eliminates repeating groups by ensuring atomic values. Second Normal Form "
        "removes partial dependencies on composite keys. Third Normal Form eliminates transitive "
        "dependencies between non-key attributes. Each successive normal form addresses specific "
        "types of update anomalies—insertion, deletion, and modification—that arise from poorly "
        "structured schemas."
    )
    return {
        "title": "Database Normalization",
        "summary": summary_text,
        "original_words": wc,
        "summary_words": len(summary_text.split()),
        "key_points": [
            "Normalization reduces data redundancy by organizing data into well-structured tables",
            "First Normal Form (1NF) requires all column values to be atomic and eliminates repeating groups",
            "Second Normal Form (2NF) builds on 1NF by removing partial dependencies on composite primary keys",
            "Third Normal Form (3NF) eliminates transitive dependencies between non-key attributes",
            "BCNF (Boyce-Codd Normal Form) is a stricter version of 3NF that handles additional edge cases",
            "Denormalization is sometimes applied deliberately for read performance at the cost of redundancy",
            "Update anomalies (insertion, deletion, modification) are the primary motivation for normalization",
        ],
        "key_terms": [
            {"term": "Normalization", "why": "Core concept—the process of structuring a relational database to reduce redundancy"},
            {"term": "Functional Dependency", "why": "Determines which attributes uniquely identify others, drives decomposition decisions"},
            {"term": "Transitive Dependency", "why": "Non-key attribute depends on another non-key attribute—eliminated in 3NF"},
            {"term": "Decomposition", "why": "Splitting tables to achieve higher normal forms while preserving data"},
            {"term": "BCNF", "why": "Strictest practical normal form, often tested in exams"},
        ],
        "topics": ["Normalization", "Normal Forms", "Functional Dependencies", "Database Design", "BCNF"],
        "flashcards": [
            {"q": "What is the primary goal of database normalization?",
             "a": "To reduce data redundancy and eliminate update anomalies (insertion, deletion, modification) by organizing data into well-structured relations."},
            {"q": "What condition must a table satisfy to be in First Normal Form (1NF)?",
             "a": "All column values must be atomic (indivisible), and there must be no repeating groups or arrays within a single row."},
            {"q": "How does 2NF differ from 1NF?",
             "a": "A table in 2NF must be in 1NF and have no partial dependencies—every non-key attribute must depend on the entire composite primary key, not just part of it."},
            {"q": "What type of dependency does Third Normal Form (3NF) eliminate?",
             "a": "Transitive dependencies, where a non-key attribute depends on another non-key attribute rather than directly on the primary key."},
            {"q": "When might a database designer choose denormalization?",
             "a": "When read performance is critical and the cost of data redundancy (extra storage, potential inconsistencies) is acceptable, such as in data warehousing or reporting systems."},
            {"q": "What is a functional dependency?",
             "a": "A relationship where one attribute uniquely determines another. Written as X → Y, meaning if two rows have the same X value, they must have the same Y value."},
            {"q": "What are update anomalies?",
             "a": "Problems that arise from poorly structured tables: insertion anomaly (can't add data without unrelated data), deletion anomaly (losing data unintentionally), and modification anomaly (inconsistent updates)."},
            {"q": "What distinguishes BCNF from 3NF?",
             "a": "BCNF requires that for every functional dependency X → Y, X must be a superkey. 3NF allows Y to be a prime attribute even if X is not a superkey."},
        ],
        "quiz": [
            {"question": "What is the primary purpose of normalization in databases?",
             "options": ["To increase data redundancy", "To reduce data redundancy and improve integrity",
                         "To speed up all queries", "To eliminate the need for indexes"],
             "answer_index": 1,
             "explanation": "Normalization reduces redundancy by organizing data into related tables with well-defined dependencies."},
            {"question": "Which normal form eliminates transitive dependencies?",
             "options": ["1NF", "2NF", "3NF", "BCNF"],
             "answer_index": 2,
             "explanation": "3NF eliminates transitive dependencies where non-key attributes depend on other non-key attributes."},
            {"question": "A table has columns (StudentID, CourseID, CourseName). StudentID+CourseID is the PK. CourseName depends only on CourseID. Which normal form is violated?",
             "options": ["1NF", "2NF", "3NF", "No violation"],
             "answer_index": 1,
             "explanation": "CourseName has a partial dependency on only CourseID (part of the composite key), violating 2NF."},
            {"question": "Which technique splits a table to achieve a higher normal form?",
             "options": ["Aggregation", "Decomposition", "Denormalization", "Replication"],
             "answer_index": 1,
             "explanation": "Decomposition splits a relation into smaller relations to eliminate anomalies while preserving data."},
            {"question": "In BCNF, for every functional dependency X → Y, what must be true about X?",
             "options": ["X must be a foreign key", "X must be a superkey",
                         "X must be a non-key attribute", "X must be a candidate key only"],
             "answer_index": 1,
             "explanation": "BCNF requires that the determinant (X) of every non-trivial functional dependency is a superkey."},
        ],
    }


def _mock_flashcards() -> list[dict]:
    return mock_summarize_result()["flashcards"][:5]


def _mock_quiz() -> list[dict]:
    return mock_summarize_result()["quiz"]
