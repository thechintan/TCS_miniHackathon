"""
pages/1_Summarize.py – Upload notes and view AI-generated summaries.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from core.ui import NOTEWISE_CSS, sidebar, page_header
from core.summarizer import summarize_note
from modules.db import init_db, save_note, get_note, save_summary, get_summary, get_notes
from modules.extract import extract_text, word_count
from modules.chat import index_note

# ── Page setup ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Summarize – NoteWise", layout="wide", initial_sidebar_state="expanded")
st.markdown(NOTEWISE_CSS, unsafe_allow_html=True)
init_db()
sidebar()

# ── Session defaults ──────────────────────────────────────────────────────
if "current_note_id" not in st.session_state:
    st.session_state.current_note_id = None
if "current_note_title" not in st.session_state:
    st.session_state.current_note_title = "No note open"
if "summary_result" not in st.session_state:
    st.session_state.summary_result = None

# ── Header ────────────────────────────────────────────────────────────────
page_header("Summarize", "Upload or paste your notes, then let AI extract what matters.")

# ── Input section ─────────────────────────────────────────────────────────
tab_upload, tab_paste = st.tabs(["Upload file", "Paste text"])

input_text = ""
input_title = ""
input_subject = ""
selected_label = ""

with tab_upload:
    uploaded = st.file_uploader(
        "Drop a TXT or PDF file here",
        type=["txt", "pdf", "png", "jpg", "jpeg"],
        label_visibility="collapsed",
    )
    if uploaded:
        input_text = extract_text(uploaded)
        input_title = os.path.splitext(uploaded.name)[0].replace("_", " ").title()
        st.markdown(f'<span class="mono" style="color: var(--muted); font-size: 0.85rem;">'
                    f'{word_count(input_text)} words extracted</span>', unsafe_allow_html=True)

with tab_paste:
    input_text_paste = st.text_area(
        "Paste your notes here",
        height=200,
        placeholder="Paste lecture notes, textbook excerpts, or any study material...",
        label_visibility="collapsed",
    )
    if input_text_paste:
        input_text = input_text_paste

# Note metadata
if input_text:
    col_t, col_s = st.columns(2)
    with col_t:
        input_title = st.text_input("Title", value=input_title or "My Notes",
                                     placeholder="e.g. DBMS Normalization")
    with col_s:
        input_subject = st.selectbox("Subject", ["DBMS", "OS", "ML", "DSA", "CN", "Other"])

# Existing note selector
notes_df = get_notes()
if not notes_df.empty:
    st.markdown("---")
    st.markdown("**Or select an existing note:**")
    note_options = {f"{r['title']} ({r['subject']})": r['id'] for _, r in notes_df.iterrows()}
    selected_label = st.selectbox("Select note", [""] + list(note_options.keys()),
                                   label_visibility="collapsed")
    if selected_label and selected_label in note_options:
        st.session_state.current_note_id = note_options[selected_label]
        note_data = get_note(st.session_state.current_note_id)
        if note_data:
            input_text = note_data["content"]
            input_title = note_data["title"]
            input_subject = note_data["subject"]
            st.session_state.current_note_title = input_title

# Summary style
st.markdown("")
style = st.radio("Summary style", ["concise", "detailed", "exam"], horizontal=True)

# ── Summarize button ──────────────────────────────────────────────────────
if st.button("Summarize"):
    if not input_text or not input_text.strip():
        st.warning("Upload a file or paste text first.")
    else:
        # Save note if new
        if st.session_state.current_note_id is None or not selected_label:
            note_id = save_note(input_title, input_subject, input_text, source="upload")
            st.session_state.current_note_id = note_id
            st.session_state.current_note_title = input_title
        else:
            note_id = st.session_state.current_note_id

        with st.spinner("Reading your notes..."):
            progress = st.progress(0)
            progress.progress(20)
            result = summarize_note(input_text, style)
            progress.progress(60)

            # Save to DB
            save_summary(
                note_id,
                result.get("summary", ""),
                result.get("key_points", []),
                result.get("flashcards", []),
                result.get("quiz", []),
                style=style,
            )
            progress.progress(80)

            # Index for RAG
            try:
                index_note(note_id, input_title, input_text)
            except Exception:
                pass
            progress.progress(100)

        st.session_state.summary_result = result
        st.rerun()

# ── Result section ────────────────────────────────────────────────────────
# Try to load from session or DB
result = st.session_state.summary_result
if result is None and st.session_state.current_note_id:
    db_summary = get_summary(st.session_state.current_note_id)
    if db_summary:
        note_data = get_note(st.session_state.current_note_id)
        result = {
            "summary": db_summary["summary"],
            "key_points": db_summary["key_points"],
            "flashcards": db_summary["flashcards"],
            "quiz": db_summary.get("quiz", []),
            "original_words": note_data["word_count"] if note_data else 0,
            "summary_words": db_summary["summary_words"],
            "topics": [],
            "key_terms": [],
        }

if result:
    st.markdown("---")
    st.markdown("## Summary")

    # Two-column layout: 65% summary, 35% sticky panel
    col_main, col_panel = st.columns([65, 35])

    with col_main:
        # Summary prose with key phrases highlighted
        summary_html = result.get("summary", "")
        key_terms = result.get("key_terms", [])
        if key_terms:
            for kt in key_terms:
                term = kt.get("term", "") if isinstance(kt, dict) else str(kt)
                why = kt.get("why", "") if isinstance(kt, dict) else ""
                if term and term.lower() in summary_html.lower():
                    import re
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    summary_html = pattern.sub(
                        f'<mark title="{why}">{term}</mark>', summary_html, count=1
                    )

        st.markdown(f'<div style="line-height: 1.75; font-size: 1.02rem;">{summary_html}</div>',
                    unsafe_allow_html=True)

        # Key points
        kps = result.get("key_points", [])
        if kps:
            st.markdown("### Key Points")
            for kp in kps:
                st.markdown(f"- {kp}")

    with col_panel:
        # Reading time saved
        orig = result.get("original_words", 0)
        summ = result.get("summary_words", len(result.get("summary", "").split()))

        if orig > 0:
            reading_saved = max(1, (orig - summ) // 200)  # ~200 wpm
            st.markdown(f'<div class="panel-label">Reading time saved</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="mono-large">{reading_saved} min</div>', unsafe_allow_html=True)
            st.markdown("")

            # Compression bar
            ratio = summ / max(orig, 1)
            pct = int(ratio * 100)
            st.markdown(f'<div class="panel-label">Compression</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="compression-bar-track">'
                f'<div class="compression-bar-fill" style="width: {pct}%;"></div>'
                f'</div>'
                f'<span class="mono" style="font-size: 0.82rem; color: var(--muted);">'
                f'Compressed {orig:,} words to {summ:,}</span>',
                unsafe_allow_html=True,
            )
            st.markdown("")

        # Topic chips
        topics = result.get("topics", [])
        if topics:
            st.markdown(f'<div class="panel-label">Topics</div>', unsafe_allow_html=True)
            chips_html = " ".join(f'<span class="topic-chip">{t}</span>' for t in topics)
            st.markdown(chips_html, unsafe_allow_html=True)
            st.markdown("")

        # Key terms list
        if key_terms:
            st.markdown(f'<div class="panel-label">Key terms</div>', unsafe_allow_html=True)
            terms_html = "<ul class='panel-terms' style='padding-left: 0;'>"
            for kt in key_terms:
                term = kt.get("term", "") if isinstance(kt, dict) else str(kt)
                terms_html += f"<li>{term}</li>"
            terms_html += "</ul>"
            st.markdown(terms_html, unsafe_allow_html=True)

    # Flashcards in expander
    flashcards = result.get("flashcards", [])
    if flashcards:
        with st.expander(f"Flashcards ({len(flashcards)} cards)"):
            for i, fc in enumerate(flashcards):
                q = fc.get("q", fc.get("question", ""))
                a = fc.get("a", fc.get("answer", ""))
                st.markdown(
                    f'<div class="flashcard">'
                    f'<div class="flashcard-counter">Card {i + 1} of {len(flashcards)}</div>'
                    f'<div class="flashcard-question">{q}</div>'
                    f'<div class="flashcard-answer">{a}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
