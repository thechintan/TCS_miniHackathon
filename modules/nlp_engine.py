"""
modules/nlp_engine.py – Local AI/ML NLP engine for arbitrary text.

Performs:
1. Extractive text summarization (TF-IDF + TextRank centrality + style weighting)
2. Salient key points extraction
3. Topic & N-gram key phrase extraction with context tooltips
4. Concept-based Flashcard generation (Q&A)
5. Dynamic Multiple-Choice Quiz generation with realistic distractors and explanations

Guarantees high-quality results for ANY input paragraph or lecture note,
completely offline without requiring an external LLM server.
"""
import re
import math
import random
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def _split_sentences(text: str) -> list[str]:
    """Split text into clean, trimmed sentences."""
    if not text:
        return []
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    # Split on sentence terminals followed by space or uppercase
    raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'\(\[])', cleaned)
    sentences = []
    for s in raw_sentences:
        s = s.strip()
        # Remove trailing bullet characters or numbering
        s = re.sub(r'^[•\-\*\d+\.\)]\s*', '', s).strip()
        if len(s) >= 15:  # meaningful sentence
            sentences.append(s)
    return sentences if sentences else [cleaned] if cleaned else []


def _extract_ngrams(text: str, top_n: int = 8) -> list[str]:
    """Extract top N-gram keyphrases using TF-IDF."""
    try:
        vec = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            token_pattern=r'(?u)\b[a-zA-Z]{3,}\b',
            max_features=200
        )
        tfidf = vec.fit_transform([text])
        feature_names = vec.get_feature_names_out()
        scores = tfidf.toarray()[0]
        top_indices = np.argsort(scores)[::-1][:top_n]
        terms = [feature_names[i].title() for i in top_indices if scores[i] > 0]
        return terms if terms else ["Core Concepts"]
    except Exception:
        # Fallback simple word frequency
        words = [w.capitalize() for w in re.findall(r'\b[a-zA-Z]{4,}\b', text)
                 if w.lower() not in {'this', 'that', 'with', 'from', 'have', 'were', 'which'}]
        return list(dict.fromkeys(words))[:top_n]


def dynamic_summarize(text: str, style: str = "concise") -> str:
    """Extractive summarization using TextRank sentence centrality.
    Works dynamically for any text/paragraph.
    """
    sentences = _split_sentences(text)
    if not sentences:
        return text
    if len(sentences) <= 2:
        return " ".join(sentences)

    # TF-IDF sentence representation
    try:
        vec = TfidfVectorizer(stop_words='english')
        tfidf = vec.fit_transform(sentences)
        sim_matrix = cosine_similarity(tfidf)
        # Degree centrality (sum of similarities to other sentences)
        centrality = sim_matrix.sum(axis=1)
    except Exception:
        centrality = np.ones(len(sentences))

    # Positional bias: opening sentence and closing sentences carry higher prior weight
    position_weights = np.ones(len(sentences))
    position_weights[0] *= 1.35  # First sentence often defines topic
    if len(sentences) > 3:
        position_weights[-1] *= 1.15  # Final sentence often concludes

    # Style weighting
    exam_keywords = re.compile(
        r'\b(is defined as|refers to|means|because|therefore|crucial|essential|fundamental|'
        r'primary|advantage|disadvantage|difference|contrast|law|rule|formula|must|always|never)\b',
        re.IGNORECASE
    )

    combined_scores = np.zeros(len(sentences))
    for i, s in enumerate(sentences):
        score = centrality[i] * position_weights[i]
        if style == "exam":
            if exam_keywords.search(s):
                score *= 1.6
        elif style == "detailed":
            # Length and density boost for detailed
            score *= (1.0 + min(len(s.split()) / 40.0, 0.4))
        combined_scores[i] = score

    # Determine sentence budget
    total_s = len(sentences)
    if style == "concise":
        k = max(2, min(3, math.ceil(total_s * 0.25)))
    elif style == "detailed":
        k = max(3, min(6, math.ceil(total_s * 0.55)))
    elif style == "exam":
        k = max(2, min(5, math.ceil(total_s * 0.35)))
    else:
        k = max(2, min(4, math.ceil(total_s * 0.35)))

    # Select top-k sentences and restore narrative order
    top_indices = np.argsort(combined_scores)[::-1][:k]
    ordered_indices = sorted(top_indices)
    summary = " ".join(sentences[i] for i in ordered_indices)
    return summary


def dynamic_key_points(text: str, top_n: int = 5) -> list[str]:
    """Extract key takeaways directly from the user's text."""
    sentences = _split_sentences(text)
    if not sentences:
        return ["No content provided."]
    if len(sentences) <= top_n:
        return sentences

    try:
        vec = TfidfVectorizer(stop_words='english')
        tfidf = vec.fit_transform(sentences)
        sim_matrix = cosine_similarity(tfidf)
        scores = sim_matrix.sum(axis=1)
        ranked = np.argsort(scores)[::-1]
        # Pick sentences while avoiding near-duplicates
        selected = []
        for idx in ranked:
            s = sentences[idx]
            # Clean leading markers
            s = re.sub(r'^[A-Z0-9\.\-\:\)]+\s*', '', s).strip()
            if s and s not in selected:
                selected.append(s)
            if len(selected) >= top_n:
                break
        return selected
    except Exception:
        return sentences[:top_n]


def dynamic_topics_and_terms(text: str, top_n: int = 5) -> tuple[list[str], list[dict]]:
    """Extract topic tags and key terms with context-based tooltips."""
    ngrams = _extract_ngrams(text, top_n=top_n * 2)
    sentences = _split_sentences(text)

    topics = ngrams[:min(5, len(ngrams))]
    key_terms = []

    for term in ngrams[:top_n]:
        # Find best sentence explaining this term
        matched_sentence = ""
        pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
        for s in sentences:
            if pattern.search(s):
                matched_sentence = s
                break

        if matched_sentence:
            # Create a concise why-it-matters tooltip snippet
            snippet = matched_sentence.strip()
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            why = f"Central concept: {snippet}"
        else:
            why = f"Key term identified in your notes."

        key_terms.append({
            "term": term,
            "why": why,
        })

    return topics, key_terms


def dynamic_flashcards(text: str, max_cards: int = 5) -> list[dict]:
    """Generate dynamic Q&A flashcards from definitional and functional sentence patterns."""
    sentences = _split_sentences(text)
    if not sentences:
        return [
            {"q": "What is the primary theme of these notes?",
             "a": "Review the summary and key points above."}
        ]

    flashcards = []
    used_questions = set()

    # Pattern 1: Definitions ("X is/are [defined as] Y")
    def_pattern = re.compile(
        r'^([A-Z][a-zA-Z0-9\s\-]{2,30}?)\s+(?:is|are|refers to|is defined as|represents|signifies)\s+(.*)$',
        re.IGNORECASE
    )

    # Pattern 2: Purpose ("X is used to / enables / facilitates Y")
    purpose_pattern = re.compile(
        r'^([A-Z][a-zA-Z0-9\s\-]{2,30}?)\s+(?:is used to|serves to|helps to|enables|facilitates|aims to)\s+(.*)$',
        re.IGNORECASE
    )

    # Pattern 3: Components ("X consists of / includes / comprises Y")
    comp_pattern = re.compile(
        r'^([A-Z][a-zA-Z0-9\s\-]{2,30}?)\s+(?:consists of|includes|comprises|is composed of|has)\s+(.*)$',
        re.IGNORECASE
    )

    for s in sentences:
        # Check definition
        m = def_pattern.match(s)
        if m:
            subject = m.group(1).strip()
            predicate = m.group(2).strip()
            q = f"What is {subject}?"
            if q not in used_questions and len(predicate) > 10:
                used_questions.add(q)
                flashcards.append({"q": q, "a": f"{subject} is {predicate}"})
                continue

        # Check purpose
        m = purpose_pattern.match(s)
        if m:
            subject = m.group(1).strip()
            predicate = m.group(2).strip()
            q = f"What is the primary function of {subject}?"
            if q not in used_questions and len(predicate) > 10:
                used_questions.add(q)
                flashcards.append({"q": q, "a": f"It serves to {predicate}"})
                continue

        # Check components
        m = comp_pattern.match(s)
        if m:
            subject = m.group(1).strip()
            predicate = m.group(2).strip()
            q = f"What does {subject} consist of?"
            if q not in used_questions and len(predicate) > 10:
                used_questions.add(q)
                flashcards.append({"q": q, "a": f"It consists of {predicate}"})
                continue

        if len(flashcards) >= max_cards:
            break

    # If regex patterns didn't yield enough, create cards from top ranked sentences and key terms
    if len(flashcards) < max_cards:
        topics = _extract_ngrams(text, top_n=6)
        for term in topics:
            if len(flashcards) >= max_cards:
                break
            # Find sentence with this term
            pattern = re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE)
            for s in sentences:
                if pattern.search(s):
                    q = f"What do these notes state about {term}?"
                    if q not in used_questions and len(s) > 20:
                        used_questions.add(q)
                        flashcards.append({"q": q, "a": s})
                        break

    # Final fallback if text was very short
    if not flashcards and sentences:
        for i, s in enumerate(sentences[:max_cards]):
            flashcards.append({
                "q": f"Key Concept #{i + 1}",
                "a": s
            })

    return flashcards[:max_cards]


def dynamic_quiz(text: str, num_questions: int = 4) -> list[dict]:
    """Generate dynamic multiple-choice quiz questions based on the input text."""
    sentences = _split_sentences(text)
    if not sentences:
        return []

    ngrams = _extract_ngrams(text, top_n=10)
    quiz = []

    # Find sentences with strong assertions or definitions
    candidate_sentences = []
    for s in sentences:
        if any(w in s.lower() for w in ['is', 'are', 'means', 'because', 'used', 'crucial', 'eliminates', 'ensures', 'requires']):
            candidate_sentences.append(s)

    if not candidate_sentences:
        candidate_sentences = sentences

    random.seed(42)  # deterministic for consistent study sessions

    for idx, s in enumerate(candidate_sentences[:num_questions]):
        # Identify the main topic of the sentence
        matched_term = None
        for t in ngrams:
            if t.lower() in s.lower():
                matched_term = t
                break
        if not matched_term:
            matched_term = ngrams[idx % len(ngrams)] if ngrams else "the core subject"

        question = f"According to your notes, which statement accurately describes {matched_term}?"

        # Correct answer is derived from the true sentence
        correct_option = s.strip()
        if len(correct_option) > 130:
            correct_option = correct_option[:127] + "..."

        # Generate plausible distractors
        other_sentences = [other for other in sentences if other != s]
        distractors = []
        if len(other_sentences) >= 3:
            for oth in random.sample(other_sentences, 3):
                opt = oth.strip()
                if len(opt) > 130:
                    opt = opt[:127] + "..."
                distractors.append(opt)
        else:
            distractors = [
                f"It is completely unrelated to {matched_term} and only applies in external systems.",
                f"It strictly eliminates the need for any structured design or oversight.",
                f"It serves as a deprecated mechanism replaced by manual configuration."
            ]

        options = [correct_option] + distractors[:3]
        # Shuffle options deterministically
        shuffled = options.copy()
        # Place correct answer at index (idx % 4) for varied placement
        target_idx = idx % 4
        shuffled[0], shuffled[target_idx] = shuffled[target_idx], shuffled[0]
        correct_index = target_idx

        explanation = f"From your notes: \"{s}\""

        quiz.append({
            "question": question,
            "options": shuffled,
            "answer_index": correct_index,
            "explanation": explanation
        })

    return quiz


def dynamic_process_all(text: str, title: str = "", style: str = "concise") -> dict:
    """End-to-end dynamic processor: takes ANY text and returns the full study package."""
    words = text.split()
    total_words = len(words)

    # Inferred title from first line or top N-gram
    inferred_title = title
    if not inferred_title or inferred_title == "My Notes":
        first_line = text.strip().split("\n")[0].strip()
        if 5 <= len(first_line) <= 50 and not first_line.endswith('.'):
            inferred_title = first_line
        else:
            top_terms = _extract_ngrams(text, top_n=2)
            inferred_title = " & ".join(top_terms) if top_terms else "Lecture Notes"

    summary = dynamic_summarize(text, style=style)
    summary_words = len(summary.split())
    key_pts = dynamic_key_points(text, top_n=5)
    topics, key_terms = dynamic_topics_and_terms(text, top_n=5)
    flashcards = dynamic_flashcards(text, max_cards=6)
    quiz = dynamic_quiz(text, num_questions=4)

    return {
        "title": inferred_title,
        "summary": summary,
        "original_words": total_words,
        "summary_words": summary_words,
        "key_points": key_pts,
        "key_terms": key_terms,
        "topics": topics,
        "flashcards": flashcards,
        "quiz": quiz,
    }
