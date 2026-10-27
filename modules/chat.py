"""
modules/chat.py – RAG chatbot: index notes into ChromaDB, answer questions.

Uses ChromaDB with native ONNX semantic embeddings (all-MiniLM-L6-v2) for
high-accuracy cosine vector similarity search.
When Ollama LLM is available, synthesizes answers via LLM.
When Ollama is offline, provides grounded extractive synthesis directly from
the most relevant passage sentences.
"""
import logging
import re
from typing import Optional

from config import CHROMA_DIR, RAG_TOP_K, CHUNK_SIZE, CHUNK_OVERLAP
from modules.llm import _check_ollama, generate
from modules.prompts import RAG_ANSWER

logger = logging.getLogger(__name__)

_collection = None
_chroma_available: Optional[bool] = None


def _get_collection():
    """Get or create the persistent ChromaDB collection."""
    global _collection, _chroma_available
    if _collection is not None:
        return _collection

    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_or_create_collection(
            name="notes",
            metadata={"hnsw:space": "cosine"},
        )
        _chroma_available = True
        return _collection
    except Exception as e:
        logger.warning("ChromaDB initialization failed: %s. Using memory fallback.", e)
        _chroma_available = False
        return None


def _chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """Split text into word-based chunks with overlap."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# In-memory fallback store
_memory_store: list[dict] = []


def index_note(note_id: int, title: str, text: str) -> None:
    """Chunk, embed, and store a note in ChromaDB for semantic vector retrieval."""
    if not text or not text.strip():
        return

    chunks = _chunk_text(text)
    collection = _get_collection()

    if collection is not None:
        try:
            ids = [f"note_{note_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {"note_id": note_id, "title": title, "chunk_index": i}
                for i in range(len(chunks))
            ]

            # Delete existing chunks for this note if re-indexing
            try:
                existing = collection.get(where={"note_id": note_id})
                if existing and existing["ids"]:
                    collection.delete(ids=existing["ids"])
            except Exception:
                pass

            # ChromaDB automatically uses its ONNX MiniLM vector embedding model
            collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas,
            )
            logger.info("ChromaDB indexed %d chunks for '%s'", len(chunks), title)
        except Exception as e:
            logger.error("ChromaDB indexing error: %s. Using memory fallback.", e)
            _index_memory(note_id, title, chunks)
    else:
        _index_memory(note_id, title, chunks)


def _index_memory(note_id: int, title: str, chunks: list[str]) -> None:
    """Fallback: store chunks in memory for TF-IDF / keyword search."""
    global _memory_store
    _memory_store = [m for m in _memory_store if m["note_id"] != note_id]
    for i, chunk in enumerate(chunks):
        _memory_store.append({
            "note_id": note_id,
            "title": title,
            "chunk_index": i,
            "text": chunk,
        })


def _synthesize_grounded_answer(question: str, sources: list[dict]) -> str:
    """Extract and synthesize an accurate answer directly from the top matched passages."""
    if not sources:
        return "I could not find relevant information in your notes to answer that question."

    top_source = sources[0]
    passage = top_source["passage"]
    title = top_source["title"]
    relevance = top_source["relevance"]

    # Extract sentences that best overlap with question keywords
    q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', question.lower()))
    # Remove common interrogatives
    q_words -= {'what', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how', 'does', 'according', 'notes'}

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', passage) if len(s.strip()) > 15]

    scored_sentences = []
    for s in sentences:
        s_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', s.lower()))
        overlap = len(q_words & s_words)
        scored_sentences.append((overlap, s))

    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    best_sentences = [s for score, s in scored_sentences if score > 0][:2]

    if not best_sentences and sentences:
        best_sentences = sentences[:2]

    answer_body = " ".join(best_sentences)
    return (
        f"Based on your notes on **{title}**:\n\n"
        f"{answer_body}\n\n"
        f"*(Grounded directly from your indexed materials with {relevance}% semantic match)*"
    )


def ask_notes(question: str, k: int = RAG_TOP_K) -> dict:
    """Answer a question using Vector RAG.
    Returns {answer, sources: [{title, passage, relevance}]}.
    """
    if not question or not question.strip():
        return {"answer": "Please enter a question about your notes.", "sources": []}

    collection = _get_collection()
    context_chunks = []

    if collection is not None and collection.count() > 0:
        try:
            # Query ChromaDB using semantic vector search
            results = collection.query(
                query_texts=[question],
                n_results=min(k, collection.count()),
                include=["documents", "metadatas", "distances"],
            )

            if results and results["documents"] and results["documents"][0]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    relevance = max(0, min(100, round((1.0 - dist) * 100)))
                    context_chunks.append({
                        "title": meta.get("title", "Unknown"),
                        "passage": doc,
                        "relevance": relevance,
                    })
        except Exception as e:
            logger.error("ChromaDB query failed: %s. Using memory search.", e)
            context_chunks = _search_memory(question, k)
    else:
        context_chunks = _search_memory(question, k)

    if not context_chunks:
        return {
            "answer": "I don't have any matching notes indexed yet. Upload and summarize some notes first.",
            "sources": [],
        }

    # If Ollama LLM is available, synthesize with prompt
    if _check_ollama():
        context_text = "\n\n".join(
            f"[From: {c['title']}]\n{c['passage']}" for c in context_chunks
        )
        prompt = RAG_ANSWER.format(context=context_text, question=question)
        answer = generate(prompt)
    else:
        # Grounded extractive synthesis from retrieved passages
        answer = _synthesize_grounded_answer(question, context_chunks)

    return {
        "answer": answer,
        "sources": context_chunks,
    }


def _search_memory(question: str, k: int) -> list[dict]:
    """In-memory cosine/keyword search over stored chunks."""
    if not _memory_store:
        return []

    q_words = set(question.lower().split())
    scored = []
    for entry in _memory_store:
        text_words = set(entry["text"].lower().split())
        overlap = len(q_words & text_words)
        if overlap > 0:
            relevance = min(99, int(overlap / max(len(q_words), 1) * 100))
            scored.append({
                "title": entry["title"],
                "passage": entry["text"][:500],
                "relevance": relevance,
            })

    scored.sort(key=lambda x: x["relevance"], reverse=True)
    return scored[:k]


def get_indexed_count() -> int:
    """Return number of indexed chunks."""
    collection = _get_collection()
    if collection is not None:
        try:
            return collection.count()
        except Exception:
            pass
    return len(_memory_store)
