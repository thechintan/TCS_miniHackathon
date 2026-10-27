"""
pages/2_Ask_Notes.py – RAG chatbot: ask questions about your notes.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from core.ui import NOTEWISE_CSS, sidebar, page_header
from modules.db import init_db, get_notes, get_note
from modules.chat import ask_notes, index_note, get_indexed_count

# ── Page setup ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Ask Notes – NoteWise", layout="wide", initial_sidebar_state="expanded")
st.markdown(NOTEWISE_CSS, unsafe_allow_html=True)
init_db()
sidebar()

# ── Session defaults ──────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_note_title" not in st.session_state:
    st.session_state.current_note_title = "No note open"
if "notes_indexed" not in st.session_state:
    st.session_state.notes_indexed = False

# ── Header ────────────────────────────────────────────────────────────────
page_header("Ask Your Notes", "Ask a question and get answers grounded in what you have uploaded.")

# ── Index notes if not done ───────────────────────────────────────────────
notes_df = get_notes()
indexed_count = get_indexed_count()

if not notes_df.empty and indexed_count == 0:
    if st.button("Index all notes for search"):
        with st.spinner("Indexing your notes for search..."):
            progress = st.progress(0)
            for i, (_, row) in enumerate(notes_df.iterrows()):
                note = get_note(int(row["id"]))
                if note:
                    index_note(int(row["id"]), note["title"], note["content"])
                progress.progress((i + 1) / len(notes_df))
            st.session_state.notes_indexed = True
        st.rerun()

# Current context
if not notes_df.empty:
    note_titles = [r["title"] for _, r in notes_df.iterrows()]
    answering_from = ", ".join(note_titles[:3])
    if len(note_titles) > 3:
        answering_from += f" and {len(note_titles) - 3} more"
    st.markdown(
        f'<p style="color: var(--muted); font-size: 0.9rem; margin-bottom: 24px;">'
        f'Answering from: {answering_from}'
        f' · {indexed_count} chunks indexed</p>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<p style="color: var(--muted); margin-top: 24px;">'
        'No notes uploaded yet. Go to <strong>Summarize</strong> to add notes first.</p>',
        unsafe_allow_html=True,
    )

# ── Chat display ──────────────────────────────────────────────────────────
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("Sources from your notes"):
                for src in msg["sources"]:
                    st.markdown(
                        f'<div style="margin-bottom: 12px; padding: 8px; '
                        f'border-bottom: 1px solid var(--border);">'
                        f'<strong>{src["title"]}</strong> '
                        f'<span class="mono-score">{src["relevance"]}% relevant</span>'
                        f'<br><span style="color: var(--muted); font-size: 0.88rem;">'
                        f'{src["passage"][:300]}{"..." if len(src["passage"]) > 300 else ""}'
                        f'</span></div>',
                        unsafe_allow_html=True,
                    )

# ── Chat input ────────────────────────────────────────────────────────────
if question := st.chat_input("Ask something about your notes..."):
    # Show user message
    st.session_state.chat_history.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    # Auto-index if needed
    if indexed_count == 0 and not notes_df.empty:
        for _, row in notes_df.iterrows():
            note = get_note(int(row["id"]))
            if note:
                index_note(int(row["id"]), note["title"], note["content"])

    # Generate answer
    with st.chat_message("assistant"):
        with st.spinner("Searching your notes..."):
            response = ask_notes(question)

        st.markdown(response["answer"])

        sources = response.get("sources", [])
        if sources:
            with st.expander("Sources from your notes"):
                for src in sources:
                    st.markdown(
                        f'<div style="margin-bottom: 12px; padding: 8px; '
                        f'border-bottom: 1px solid var(--border);">'
                        f'<strong>{src["title"]}</strong> '
                        f'<span class="mono-score">{src["relevance"]}% relevant</span>'
                        f'<br><span style="color: var(--muted); font-size: 0.88rem;">'
                        f'{src["passage"][:300]}{"..." if len(src["passage"]) > 300 else ""}'
                        f'</span></div>',
                        unsafe_allow_html=True,
                    )

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response["answer"],
        "sources": sources,
    })
