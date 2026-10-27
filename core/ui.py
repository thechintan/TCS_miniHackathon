"""
core/ui.py – Page setup, CSS injection, and sidebar for NoteWise.
"""
import streamlit as st


# ── CSS ───────────────────────────────────────────────────────────────────

NOTEWISE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Newsreader:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

:root {
    --bg: #FAF8F4;
    --surface: #FFFFFF;
    --border: #E6E2DA;
    --text: #1A1A1A;
    --muted: #6B6B6B;
    --accent: #1F3A5F;
    --highlight-key: #FFF3B0;
    --highlight-warn: #FFD6D6;
    --font-heading: 'Newsreader', Georgia, serif;
    --font-body: 'Instrument Sans', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', 'Courier New', monospace;
    --radius: 6px;
    --sp-1: 4px;
    --sp-2: 8px;
    --sp-3: 16px;
    --sp-4: 24px;
    --sp-5: 48px;
    --sp-6: 96px;
    --transition: 150ms ease;
}

/* ── Global resets ──────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: var(--font-body) !important;
    color: var(--text) !important;
}

.stApp {
    background-color: var(--bg) !important;
}

/* ── Main content width ─────────────────────────────────────────────── */
.block-container {
    max-width: 960px !important;
    padding-left: var(--sp-4) !important;
    padding-right: var(--sp-4) !important;
    padding-top: var(--sp-5) !important;
}

/* ── Typography ─────────────────────────────────────────────────────── */
h1, h2, h3 {
    font-family: var(--font-heading) !important;
    color: var(--text) !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
}

h1 {
    font-size: 2.2rem !important;
    line-height: 1.2 !important;
    margin-bottom: var(--sp-2) !important;
}

h2 {
    font-size: 1.5rem !important;
    line-height: 1.3 !important;
    margin-top: var(--sp-5) !important;
    margin-bottom: var(--sp-3) !important;
}

h3 {
    font-size: 1.15rem !important;
    line-height: 1.4 !important;
    margin-top: var(--sp-4) !important;
    margin-bottom: var(--sp-2) !important;
}

p, li, span, div {
    font-family: var(--font-body) !important;
    line-height: 1.65 !important;
}

.subline {
    color: var(--muted);
    font-size: 1.05rem;
    margin-top: 0;
    margin-bottom: var(--sp-5);
    font-family: var(--font-body);
    line-height: 1.5;
}

/* ── Mono numbers ───────────────────────────────────────────────────── */
.mono {
    font-family: var(--font-mono) !important;
    font-weight: 500;
}

.mono-large {
    font-family: var(--font-mono) !important;
    font-size: 2.4rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1;
}

.mono-score {
    font-family: var(--font-mono) !important;
    font-size: 1rem;
    color: var(--accent);
}

/* ── Key phrase highlight (marker pen) ──────────────────────────────── */
mark, .key-phrase {
    background-color: var(--highlight-key) !important;
    color: var(--text) !important;
    padding: 1px 4px;
    border-radius: 2px;
    cursor: help;
    transition: opacity var(--transition);
}

.weak-highlight {
    background-color: var(--highlight-warn) !important;
    color: var(--text) !important;
    padding: 1px 4px;
    border-radius: 2px;
}

/* ── Sidebar ────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: var(--sp-4) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] {
    font-family: var(--font-body) !important;
}

.sidebar-brand {
    font-family: var(--font-heading);
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: var(--sp-1);
    letter-spacing: -0.01em;
}

.sidebar-meta {
    font-family: var(--font-body);
    font-size: 0.82rem;
    color: var(--muted);
    line-height: 1.5;
    margin-bottom: var(--sp-4);
}

/* ── Buttons ────────────────────────────────────────────────────────── */
.stButton > button {
    background-color: var(--accent) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: var(--sp-2) var(--sp-4) !important;
    transition: opacity var(--transition) !important;
    box-shadow: none !important;
}

.stButton > button:hover {
    opacity: 0.85 !important;
    box-shadow: none !important;
}

/* Secondary / ghost buttons */
.stButton > button[kind="secondary"],
div[data-testid="stFormSubmitButton"] > button {
    background-color: var(--accent) !important;
    color: #FFFFFF !important;
}

/* ── File uploader ──────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 1px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    padding: var(--sp-4) !important;
    background-color: var(--surface) !important;
}

[data-testid="stFileUploader"] section {
    border: none !important;
}

/* ── Input fields ───────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-body) !important;
    background-color: var(--surface) !important;
    transition: border-color var(--transition) !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: none !important;
}

/* ── Radio buttons ──────────────────────────────────────────────────── */
.stRadio > div {
    gap: var(--sp-2) !important;
}

.stRadio > div > label {
    font-family: var(--font-body) !important;
    padding: var(--sp-1) var(--sp-2) !important;
    border-radius: var(--radius) !important;
    transition: background-color var(--transition) !important;
}

/* ── Tabs ───────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    border-bottom: 1px solid var(--border) !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: var(--font-body) !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    border-bottom: 2px solid transparent !important;
    padding: var(--sp-2) var(--sp-3) !important;
    transition: color var(--transition), border-color var(--transition) !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}

/* ── Expander ───────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    font-family: var(--font-body) !important;
    font-weight: 500 !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    background-color: var(--surface) !important;
}

/* ── Metric cards ───────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: var(--sp-3) !important;
}

[data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-weight: 600 !important;
    color: var(--accent) !important;
}

[data-testid="stMetricLabel"] {
    font-family: var(--font-body) !important;
    color: var(--muted) !important;
    font-size: 0.85rem !important;
}

/* ── Divider ────────────────────────────────────────────────────────── */
hr, [data-testid="stHorizontalRule"] {
    border-color: var(--border) !important;
    border-width: 1px 0 0 0 !important;
    margin: var(--sp-5) 0 !important;
}

/* ── Table (hairline dividers, no zebra) ────────────────────────────── */
.stDataFrame, .stTable {
    font-family: var(--font-body) !important;
}

table {
    border-collapse: collapse !important;
    width: 100% !important;
}

table th {
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    color: var(--muted) !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    border-bottom: 1px solid var(--border) !important;
    padding: var(--sp-2) var(--sp-2) !important;
    background: transparent !important;
}

table td {
    font-family: var(--font-body) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: var(--sp-2) var(--sp-2) !important;
    background: transparent !important;
    color: var(--text) !important;
}

table tr:hover td {
    background-color: rgba(31, 58, 95, 0.03) !important;
}

/* ── Chat messages ──────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: var(--sp-3) !important;
    margin-bottom: var(--sp-2) !important;
    font-family: var(--font-body) !important;
}

/* ── Topic chips ────────────────────────────────────────────────────── */
.topic-chip {
    display: inline-block;
    padding: 2px var(--sp-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 0.82rem;
    font-family: var(--font-body);
    color: var(--muted);
    margin: 2px 4px 2px 0;
    background: var(--surface);
    transition: border-color var(--transition);
}

/* ── Compression bar ────────────────────────────────────────────────── */
.compression-bar-track {
    width: 100%;
    height: 6px;
    background: var(--border);
    border-radius: 3px;
    overflow: hidden;
    margin: var(--sp-2) 0;
}

.compression-bar-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 3px;
    transition: width var(--transition);
}

/* ── Flashcard ──────────────────────────────────────────────────────── */
.flashcard {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-4);
    margin: var(--sp-3) 0;
}

.flashcard-question {
    font-family: var(--font-heading);
    font-size: 1.25rem;
    font-weight: 500;
    color: var(--text);
    line-height: 1.4;
    margin-bottom: var(--sp-3);
}

.flashcard-answer {
    font-family: var(--font-body);
    color: var(--text);
    line-height: 1.6;
    padding-top: var(--sp-3);
    border-top: 1px solid var(--border);
}

.flashcard-counter {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: var(--muted);
}

/* ── Sticky panel ───────────────────────────────────────────────────── */
.sticky-panel {
    position: sticky;
    top: var(--sp-5);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-4);
}

.panel-label {
    font-family: var(--font-body);
    font-size: 0.78rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: var(--sp-1);
}

.panel-terms {
    font-family: var(--font-body);
    font-size: 0.9rem;
    color: var(--text);
    line-height: 1.8;
}

.panel-terms li {
    border-bottom: 1px solid var(--border);
    padding: var(--sp-1) 0;
    list-style: none;
}

/* ── Loading ────────────────────────────────────────────────────────── */
.stSpinner > div {
    font-family: var(--font-body) !important;
    color: var(--muted) !important;
}

[data-testid="stStatusWidget"] {
    font-family: var(--font-body) !important;
}

/* ── Progress bar ───────────────────────────────────────────────────── */
.stProgress > div > div > div {
    background-color: var(--accent) !important;
    height: 3px !important;
}

/* ── Hide Streamlit branding ────────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* ── Form styling ───────────────────────────────────────────────────── */
[data-testid="stForm"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: var(--sp-4) !important;
    background-color: var(--surface) !important;
}
</style>
"""


def page_setup(title: str = "NoteWise", icon: str = ""):
    """Configure Streamlit page and inject CSS. Call once per page."""
    st.set_page_config(
        page_title=title,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(NOTEWISE_CSS, unsafe_allow_html=True)


def sidebar():
    """Render the NoteWise sidebar."""
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">NoteWise</div>', unsafe_allow_html=True)

        # Current note title
        current_title = st.session_state.get("current_note_title", "No note open")
        model_status = _get_model_status()
        st.markdown(
            f'<div class="sidebar-meta">{current_title}<br>{model_status}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")


def page_header(title: str, subline: str):
    """Render a page title with subline."""
    st.markdown(f"# {title}")
    st.markdown(f'<p class="subline">{subline}</p>', unsafe_allow_html=True)


def _get_model_status() -> str:
    """Check model availability and return a status line."""
    try:
        import ollama as _ol
        models = _ol.list()
        model_names = [m.get("name", "") if isinstance(m, dict) else str(m) for m in models.get("models", [])]
        if any("llama" in n.lower() or "phi" in n.lower() for n in model_names):
            return "LLM connected"
        return "LLM available (pull a model)"
    except Exception:
        return "Running with mock data"
