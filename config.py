# ── Config ────────────────────────────────────────────────────────────────
import os

# Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "notes.db")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_data")
CACHE_PATH = os.path.join(BASE_DIR, "demo", "cached_summaries.json")

# LLM
LLM_TEMPERATURE = 0.2
CHUNK_SIZE = 1500       # words per chunk
CHUNK_OVERLAP = 50      # word overlap
RAG_TOP_K = 3

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)
