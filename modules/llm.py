"""
modules/llm.py – Thin Ollama wrapper with graceful fallback.
"""
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_ollama_available: Optional[bool] = None


def _check_ollama():
    """Check once whether Ollama is reachable."""
    global _ollama_available
    if _ollama_available is not None:
        return _ollama_available
    try:
        import ollama as _ol
        _ol.list()
        _ollama_available = True
    except Exception:
        _ollama_available = False
        logger.warning("Ollama is not available – using mock responses.")
    return _ollama_available


def generate(prompt: str, model: str | None = None, temperature: float = 0.2,
             system: str = "") -> str:
    """Send a prompt to Ollama and return the text response.
    Falls back to a placeholder if Ollama is unavailable."""
    from config import LLM_MODEL, OLLAMA_HOST
    model = model or LLM_MODEL

    if not _check_ollama():
        return _mock_generate(prompt)

    try:
        import ollama as _ol
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = _ol.chat(
            model=model,
            messages=messages,
            options={"temperature": temperature},
        )
        return resp["message"]["content"]
    except Exception as e:
        logger.error("Ollama generate failed: %s", e)
        return _mock_generate(prompt)


def generate_json(prompt: str, model: str | None = None,
                  temperature: float = 0.2, system: str = "") -> dict | list:
    """Generate and parse JSON from the LLM. Retries once on parse failure."""
    raw = generate(prompt, model=model, temperature=temperature, system=system)
    # Try to extract JSON from the response
    return _parse_json_response(raw)


def _parse_json_response(raw: str) -> dict | list:
    """Extract JSON from LLM output (handles markdown fences etc.)."""
    text = raw.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # drop opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON array or object in the text
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    continue
        logger.warning("Could not parse JSON from LLM output.")
        return {}


def get_embeddings(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Get embeddings for a list of texts via Ollama."""
    from config import EMBED_MODEL
    model = model or EMBED_MODEL

    if not _check_ollama():
        return _mock_embeddings(texts)

    try:
        import ollama as _ol
        results = []
        for text in texts:
            resp = _ol.embeddings(model=model, prompt=text)
            results.append(resp["embedding"])
        return results
    except Exception as e:
        logger.error("Ollama embeddings failed: %s", e)
        return _mock_embeddings(texts)


# ── Mock fallbacks ────────────────────────────────────────────────────────

def _mock_generate(prompt: str) -> str:
    """Return a context-aware mock response."""
    p = prompt.lower()
    if "summarize" in p or "summary" in p:
        return (
            "This document covers the fundamental concepts of the subject matter. "
            "The key ideas include the core definitions, theoretical foundations, "
            "and practical applications discussed in class. Important relationships "
            "between concepts are highlighted, along with relevant examples. "
            "Students should focus on understanding the underlying principles "
            "rather than memorizing specific details."
        )
    if "key point" in p or "key_point" in p or "bullet" in p:
        return json.dumps([
            "Core definitions and terminology are essential for understanding the subject",
            "The theoretical framework provides the basis for practical applications",
            "Multiple examples demonstrate real-world usage of these concepts",
            "Common misconceptions are addressed with clarifying explanations",
            "Practice problems reinforce understanding of key principles"
        ])
    if "flashcard" in p:
        return json.dumps([
            {"q": "What is the primary purpose of this concept?",
             "a": "To provide a structured approach to organizing and understanding information."},
            {"q": "How does this technique differ from traditional methods?",
             "a": "It uses systematic analysis rather than ad-hoc approaches."},
            {"q": "What are the three main components?",
             "a": "Definition, application, and evaluation."},
            {"q": "When should this approach be applied?",
             "a": "When dealing with complex, multi-faceted problems."},
            {"q": "What is the most common mistake students make?",
             "a": "Confusing correlation with causation in the analysis."},
        ])
    if "quiz" in p or "mcq" in p:
        return json.dumps([
            {"question": "What is the primary purpose of normalization in databases?",
             "options": ["To increase data redundancy", "To reduce data redundancy and improve integrity",
                         "To speed up all queries", "To eliminate the need for indexes"],
             "answer_index": 1, "explanation": "Normalization reduces redundancy by organizing data into related tables."},
            {"question": "Which normal form eliminates transitive dependencies?",
             "options": ["1NF", "2NF", "3NF", "BCNF"],
             "answer_index": 2, "explanation": "3NF eliminates transitive dependencies where non-key attributes depend on other non-key attributes."},
            {"question": "What does ACID stand for in database transactions?",
             "options": ["Atomicity, Consistency, Isolation, Durability",
                         "Addition, Computation, Integration, Delivery",
                         "Atomic, Complete, Integrated, Durable",
                         "Access, Control, Identity, Data"],
             "answer_index": 0, "explanation": "ACID properties ensure reliable transaction processing in databases."},
            {"question": "Which technique splits a table to reduce redundancy?",
             "options": ["Aggregation", "Decomposition", "Denormalization", "Replication"],
             "answer_index": 1, "explanation": "Decomposition splits a relation into smaller relations to eliminate anomalies."},
            {"question": "A relation is in 2NF if it is in 1NF and what other condition?",
             "options": ["No multi-valued dependencies", "No partial key dependencies",
                         "No transitive dependencies", "No functional dependencies"],
             "answer_index": 1, "explanation": "2NF requires that every non-key attribute is fully functionally dependent on the entire primary key."},
        ])
    if "answer" in p or "question" in p:
        return (
            "Based on your notes, the answer involves understanding the key relationships "
            "between the concepts discussed. The notes specifically mention that the proper "
            "approach requires systematic analysis of the components involved."
        )
    return "This is a mock response. Connect Ollama for real AI-generated content."


def _mock_embeddings(texts: list[str]) -> list[list[float]]:
    """Return deterministic mock embeddings."""
    import hashlib
    results = []
    for text in texts:
        h = hashlib.md5(text.encode()).hexdigest()
        # Generate a 384-dimensional vector from the hash
        vec = []
        for i in range(0, len(h), 2):
            val = int(h[i:i + 2], 16) / 255.0 - 0.5
            vec.append(val)
        # Pad to 384 dimensions
        while len(vec) < 384:
            vec.extend(vec[:384 - len(vec)])
        results.append(vec[:384])
    return results
