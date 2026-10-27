# Smart Notes Summarizer: Product Requirements Document

**Event:** TCS Technology Day Hackathon (Use Case 6) | **Duration:** 1 hour | **Team size:** 4 | **Version:** 1.0

---

## 1. Overview

**Smart Notes Summarizer** is an AI-enabled web app that helps university students turn long, messy class notes into short summaries, key points, flashcards and quizzes. It also lets them chat with their notes, track their study progress on a dashboard, and download a study report.

The prototype runs fully locally (Ollama + SQLite + ChromaDB), so it needs no internet or paid API during the demo.

## 2. Problem Statement

University students need intelligent digital tools to improve learning, productivity, career readiness, collaboration and campus experience. In practice, students collect large volumes of notes (lecture slides, PDFs, handwritten pages) across many subjects. Revising from them is slow, unstructured and hard to measure.

## 3. Business Requirement (from the problem sheet)

Design and develop Smart Notes Summarizer as an AI-enabled solution with:

| Required capability | How we meet it |
| --- | --- |
| Automation | Auto-extract text, auto-summarize, auto-generate flashcards and quizzes |
| Recommendations | Weak topics to revise, suggested flashcards and quiz questions |
| Analytics | Dashboard with notes per subject, compression ratio, quiz scores |
| Conversational assistance | RAG chatbot that answers questions from the student's own notes |

**Scope:** web-based prototype with sample datasets, dashboards, reports and AI-powered insights, suitable for hackathons and student projects.

## 4. Goals and Non-Goals

### Goals

- Working end-to-end demo in 60 minutes
- Summarize any note (paste, TXT, PDF; image is a bonus) in under 15 seconds
- Answer questions grounded in the uploaded notes
- Show meaningful analytics from sample university data
- Export a downloadable study report

### Non-Goals (out of scope for this hour)

- User login, authentication and multi-user accounts
- Cloud deployment, mobile app
- Real-time collaboration (mentioned as future scope only)
- Fine-tuning any model

## 5. Target Users

| Persona | Need |
| --- | --- |
| **Aarav, 2nd-year CS student** | Has 40 pages of DBMS notes the night before the exam and wants a quick revision sheet |
| **Priya, 3rd-year student** | Wants to test herself and see which topics she is weak in |
| **Study group** | Wants one shareable study sheet per subject |

## 6. Features and Priorities

Priority key: **P0** = must have for demo, **P1** = should have, **P2** = bonus if time remains.

| ID | Feature | Description | Priority |
| --- | --- | --- | --- |
| F1 | Notes input | Paste text or upload TXT/PDF; load sample notes with one click | P0 |
| F2 | Summary | Short summary (5 to 7 lines) of the note | P0 |
| F3 | Key points | Bullet list of the important points and terms | P0 |
| F4 | Flashcards | 5 Q/A flashcards generated per note | P1 |
| F5 | Quiz | 5 MCQs with answers, scored in the UI; score saved | P1 |
| F6 | Chat with notes | RAG chatbot, answers with the source note name | P0 |
| F7 | Dashboard | Charts: notes per subject, word counts, compression ratio, quiz scores | P0 |
| F8 | Recommendations | "Revise these topics" based on low quiz scores | P1 |
| F9 | Report export | Download study sheet as Markdown (PDF optional) | P1 |
| F10 | Image notes (OCR) | Photo of handwritten/printed notes via OpenCV + pytesseract | P2 |
| F11 | Summary style toggle | Short / detailed / ELI5 | P2 |

## 7. User Flow

1. Student opens the app and lands on **Upload**.
2. Student pastes text, uploads a file, or clicks **Load Sample Data**.
3. App extracts text, stores the note in SQLite, and indexes chunks in ChromaDB.
4. Student opens **Summary**, picks a note, and clicks **Summarize**. Summary, key points and flashcards appear.
5. Student opens **Quiz**, takes the MCQs, and sees the score. Score is saved.
6. Student opens **Chat** and asks, "What is normalization?" The bot answers from the notes and cites the source.
7. Student opens **Dashboard** to see analytics and recommended topics to revise.
8. Student opens **Reports** and downloads the study sheet.

## 8. System Architecture

```
┌──────────────────────────── Streamlit UI (app.py) ────────────────────────────┐
│  Upload │ Summary │ Quiz │ Chat │ Dashboard │ Reports                         │
└───────┬──────────┬────────┬───────┬──────────┬──────────────┬─────────────────┘
        │          │        │       │          │              │
  extract.py   summarizer.py │    chat.py   dashboard.py  report.py
  (PDF/TXT/OCR)  (LLM calls) │   (RAG)      (Pandas+charts) (export)
        │          │        │       │          │              │
        └──────────┴────────┴───────┴────┬─────┴──────────────┘
                                         │
                    db.py (SQLite)   ChromaDB (vectors)   Ollama (LLM)
```

**Data flow:** Upload → `extract_text()` → `db.save_note()` + `chat.index_note()` → `summarizer.*()` → `db.save_summary()` → dashboard and report read from SQLite.

## 9. Tech Stack

| Layer | Tool | Reason |
| --- | --- | --- |
| UI + backend | Streamlit (Python) | Fastest way to build a web prototype |
| LLM | Ollama with `llama3.2:3b` or `phi3` | Local, free, fast enough on a laptop |
| Embeddings | Ollama `nomic-embed-text` (or `sentence-transformers`) | Local embeddings for RAG |
| Vector store | ChromaDB (FAISS as alternative) | Simple persistent vector search |
| Database | SQLite | Zero setup |
| Data/analytics | Pandas | Aggregations for the dashboard |
| Charts | Streamlit native charts or Plotly | Quick and interactive |
| PDF reading | PyPDF2 or pypdf | Text extraction |
| OCR (bonus) | OpenCV + pytesseract | Image notes |
| Report | Markdown string (optional: fpdf2 for PDF) | Easy download |

## 10. Folder Structure

```
smart-notes/
├── app.py                  # Streamlit entry point, navigation, wiring (Person 1)
├── requirements.txt        # All dependencies (Person 1)
├── README.md               # Setup and run instructions (Person 4)
├── config.py               # Model names, paths, constants (Person 1)
│
├── modules/
│   ├── __init__.py
│   ├── extract.py          # extract_text(file) for PDF, TXT, image (Person 3)
│   ├── summarizer.py       # summarize, key_points, flashcards, quiz (Person 2)
│   ├── prompts.py          # All LLM prompt templates (Person 2)
│   ├── llm.py              # Thin Ollama wrapper: generate(prompt) (Person 2)
│   ├── chat.py             # index_note, ask_notes using ChromaDB (Person 3)
│   ├── db.py               # SQLite setup and CRUD helpers (Person 4)
│   ├── dashboard.py        # Pandas + chart functions (Person 4)
│   └── report.py           # build_report(note_id) -> Markdown/PDF (Person 4)
│
├── pages/                  # Optional: Streamlit multipage files
│   ├── 1_Upload.py
│   ├── 2_Summary.py
│   ├── 3_Quiz.py
│   ├── 4_Chat.py
│   ├── 5_Dashboard.py
│   └── 6_Reports.py
│
├── sample_data/
│   ├── dbms_normalization.txt
│   ├── dbms_transactions.txt
│   ├── os_scheduling.txt
│   ├── os_deadlocks.txt
│   ├── ml_supervised.txt
│   ├── ml_overfitting.txt
│   └── sample_quiz_scores.csv   # Seed data so the dashboard looks rich
│
├── data/                   # Created at runtime (git-ignored)
│   ├── notes.db            # SQLite database
│   └── chroma/             # ChromaDB persistent folder
│
├── demo/
│   ├── pitch.pptx          # Final presentation (Person 4)
│   ├── demo_script.md      # Step-by-step demo script
│   └── cached_summaries.json   # Fallback if the LLM is slow
│
└── .gitignore
```

**Rule:** use either `pages/` (multipage) or a single `app.py` with a sidebar radio. For a 1-hour build, the **single `app.py` with a sidebar radio** is recommended, so the `pages/` folder can be skipped.

## 11. Data Model (SQLite)

```sql
CREATE TABLE IF NOT EXISTS notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    subject     TEXT NOT NULL,
    content     TEXT NOT NULL,
    word_count  INTEGER,
    source      TEXT,              -- 'sample', 'paste', 'pdf', 'image'
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS summaries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id       INTEGER REFERENCES notes(id),
    summary       TEXT,
    key_points    TEXT,            -- JSON list
    flashcards    TEXT,            -- JSON list of {q, a}
    summary_words INTEGER,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quiz_scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id     INTEGER REFERENCES notes(id),
    score       INTEGER,
    total       INTEGER,
    taken_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 12. Module Contracts (agree on these in the first 10 minutes)

Every person codes against these exact signatures so integration is painless.

### `modules/extract.py` (Person 3)

```python
def extract_text(uploaded_file) -> str:
    """Accepts a Streamlit UploadedFile (txt/pdf/png/jpg). Returns plain text."""
```

### `modules/summarizer.py` (Person 2)

```python
def summarize(text: str, style: str = "short") -> str
def key_points(text: str) -> list[str]
def generate_flashcards(text: str, n: int = 5) -> list[dict]   # [{"q":..., "a":...}]
def generate_quiz(text: str, n: int = 5) -> list[dict]
# quiz item: {"question":..., "options":[A,B,C,D], "answer":"B", "topic":...}
```

### `modules/chat.py` (Person 3)

```python
def index_note(note_id: int, title: str, text: str) -> None   # chunk + embed + store
def ask_notes(question: str, k: int = 3) -> dict
# returns {"answer": str, "sources": [note titles]}
```

### `modules/db.py` (Person 4)

```python
def init_db() -> None
def save_note(title, subject, content, source) -> int          # returns note_id
def get_notes() -> pandas.DataFrame
def get_note(note_id) -> dict
def save_summary(note_id, summary, key_points, flashcards) -> None
def get_summary(note_id) -> dict | None
def save_quiz_score(note_id, score, total) -> None
def get_quiz_scores() -> pandas.DataFrame
def load_sample_data() -> int                                   # loads sample_data/, returns count
```

### `modules/dashboard.py` (Person 4)

```python
def render_dashboard() -> None        # draws all charts and KPIs using Streamlit
def get_weak_topics() -> list[str]    # subjects/topics with lowest quiz average
```

### `modules/report.py` (Person 4)

```python
def build_report(note_id: int) -> str    # Markdown study sheet
def build_full_report() -> str           # All notes, all subjects
```

## 13. AI Design

### Model setup

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### Prompt rules (Person 2)

- Keep prompts short and explicit, and tell the model the exact output format.
- For flashcards and quiz, ask for **JSON only** and parse it with a safe fallback (`try/except`, retry once).
- **Long notes:** split text into chunks of about 1,500 words, summarize each chunk, then summarize the summaries (map-reduce).
- Temperature low (0.2) for factual output.

### Example summary prompt

```
You are a study assistant. Summarize the notes below in 5 to 7 lines for a
university student. Use simple language. Do not add information that is not in the notes.

NOTES:
{text}
```

### RAG pipeline (Person 3)

1. **Chunk** each note into about 300-word pieces with 50-word overlap.
2. **Embed** each chunk and store in ChromaDB with metadata `{note_id, title, subject}`.
3. **Retrieve** top-k (3) chunks for the question.
4. **Generate** answer with prompt: "Answer only from the context. If the answer is not in the context, say you don't know."
5. **Return** answer plus source titles.

## 14. UI Specification

Sidebar navigation (radio): **Upload | Summary | Quiz | Chat | Dashboard | Reports**

| Page | Elements |
| --- | --- |
| **Upload** | Subject dropdown, title input, text area, file uploader, **Load Sample Data** button, list of saved notes |
| **Summary** | Note selector, **Summarize** button, tabs for Summary / Key Points / Flashcards, word-count reduction badge |
| **Quiz** | Note selector, 5 MCQs with radio buttons, **Submit**, score display, saved to DB |
| **Chat** | Chat window (`st.chat_message`), input box, source chips under each answer |
| **Dashboard** | KPI cards (total notes, avg compression, avg quiz score), bar chart (notes per subject), line chart (quiz score over time), table of weak topics with "Revise this" suggestions |
| **Reports** | Choose a note or all notes, preview Markdown, **Download** button |

Use `st.session_state` for the selected note, the quiz state and the chat history.

## 15. Dashboard Metrics (Person 4)

- Total notes, total words processed
- Notes per subject (bar chart)
- Average compression ratio = `1 - summary_words / note_words` (KPI)
- Quiz score per attempt over time (line chart)
- Average score per subject (bar chart)
- **Recommendation panel:** subjects with average score below 60% flagged as "Revise"

## 16. Team Roles and Responsibilities

| Person | Role | Owns | Deliverable |
| --- | --- | --- | --- |
| **P1** | Frontend + backend lead | `app.py`, `config.py`, `requirements.txt`, integration, UI polish, session state | Running app skeleton by minute 15, fully integrated app by minute 50 |
| **P2** | AI/LLM engineer | `llm.py`, `summarizer.py`, `prompts.py` | Summary, key points, flashcards, quiz functions returning clean data |
| **P3** | Chatbot, RAG and OCR engineer | `chat.py`, `extract.py` | `ask_notes()` and `extract_text()` working; OCR if time permits |
| **P4** | Data, analytics and demo lead | `db.py`, `dashboard.py`, `report.py`, `sample_data/`, `demo/` | Sample data, DB, dashboard, report export, pitch deck, demo script |

**Dependency note:** P4 should finish `db.py` and sample data first (by minute 15), because P1 and P2 need it. P1 can use mock functions until each module lands.

## 17. Timeline (60 minutes)

| Minutes | Activity | Who |
| --- | --- | --- |
| 0 to 10 | Create repo, agree on folder structure and contracts (Section 12), install dependencies, pull Ollama models | All |
| 10 to 25 | P1: skeleton with all 6 pages and mock data. P2: `llm.py` + `summarize`. P3: `extract_text` + chunking. P4: `db.py` + sample notes | Parallel |
| 25 to 40 | P2: key points, flashcards, quiz. P3: ChromaDB + `ask_notes`. P4: dashboard + report. P1: connects finished modules | Parallel |
| 40 to 50 | Integration, bug fixing, replace mocks with real calls | All |
| 50 to 57 | End-to-end test of the demo flow (Section 20), cache fallback summaries | All |
| 57 to 60 | Final pitch rehearsal | All |

**Cut order if running late:** drop OCR first, then the PDF report (keep Markdown), then the style toggle, then flashcards.

## 18. Setup Instructions

```bash
git clone <repo-url> && cd smart-notes
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
ollama pull llama3.2:3b
ollama pull nomic-embed-text
streamlit run app.py
```

### `requirements.txt`

```
streamlit
ollama
chromadb
pandas
plotly
pypdf
opencv-python
pytesseract
fpdf2
```

## 19. Non-Functional Requirements

| Area | Requirement |
| --- | --- |
| Performance | Summary in under 15 seconds on a laptop; chat reply in under 10 seconds |
| Reliability | App must not crash on bad LLM output (safe JSON parsing, friendly error messages) |
| Privacy | All data stays local; no external API calls |
| Usability | Maximum 3 clicks from landing to first summary |
| Portability | Runs on Windows, macOS and Linux with the setup above |

## 20. Demo Script (3 to 4 minutes)

1. **Hook (20 s):** "Students have too many notes and too little time to revise."
2. **Load sample data (15 s):** click Load Sample Data; show the 6 notes across DBMS, OS and ML.
3. **Summarize (45 s):** pick the DBMS Normalization note, click Summarize, show summary, key points and flashcards, and the word-reduction badge.
4. **Quiz (30 s):** take a quick quiz, submit, show the score being saved.
5. **Chat (45 s):** ask "What is the difference between 2NF and 3NF?" and show the answer with sources.
6. **Dashboard (45 s):** show notes per subject, quiz trend and the "Revise OS Deadlocks" recommendation.
7. **Report (20 s):** download the study sheet.
8. **Close (20 s):** future scope (Section 22).

## 21. Risks and Mitigation

| Risk | Impact | Mitigation |
| --- | --- | --- |
| LLM is slow on a weak laptop | Demo lags | Use a 3B model, keep `cached_summaries.json` as fallback |
| LLM returns invalid JSON | Quiz or flashcards break | `try/except`, retry once, then show a default set |
| Integration conflicts | Lost time | Fixed function contracts, separate files per person, frequent small commits |
| ChromaDB or Ollama install issues | RAG blocked | Fallback to FAISS or simple TF-IDF retrieval (scikit-learn) |
| OCR setup (Tesseract binary) fails | Image upload unusable | Treat OCR as P2; skip if not working by minute 40 |
| Wi-Fi unreliable at venue | Model download fails | Pull all models before the event |

## 22. Success Criteria and Future Scope

### Success criteria

- Full demo flow (Section 20) works without errors
- All P0 features are working
- Dashboard shows real data computed from SQLite
- Chat answers come from the notes and cite sources
- Team can explain the architecture and AI approach clearly

### Future scope (mention in the pitch)

- Multi-language notes and voice-note transcription
- Collaborative shared notebooks for study groups
- Spaced-repetition scheduler for flashcards
- Career readiness links: map notes to skills and interview questions
- LMS integration (Moodle, Google Classroom)
- Mobile app and cloud deployment

## 23. Git and Collaboration Rules

- One shared repo; each person works only in their own files to avoid merge conflicts.
- Commit small and often; push at minutes 25, 40 and 50.
- Only P1 edits `app.py`; others send function-ready code.
- Use a shared group chat for blockers; ask for help after 5 minutes stuck.
