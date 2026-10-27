"""
app.py – NoteWise: Smart Notes Summarizer
Entry point and History page.
"""
import sys
import os
import streamlit as st

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ui import NOTEWISE_CSS, sidebar
from modules.db import init_db, get_notes, get_note, load_sample_data

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NoteWise",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(NOTEWISE_CSS, unsafe_allow_html=True)

# ── Init DB ───────────────────────────────────────────────────────────────
init_db()

# ── Sidebar ───────────────────────────────────────────────────────────────
sidebar()

# ── Session defaults ──────────────────────────────────────────────────────
if "current_note_id" not in st.session_state:
    st.session_state.current_note_id = None
if "current_note_title" not in st.session_state:
    st.session_state.current_note_title = "No note open"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── History page ──────────────────────────────────────────────────────────
st.markdown("# Your Notes")
st.markdown('<p class="subline">A library of everything you have summarized so far.</p>', unsafe_allow_html=True)

# Load sample data button
col_action, col_spacer = st.columns([1, 3])
with col_action:
    if st.button("Load sample data"):
        with st.spinner("Loading sample notes..."):
            count = load_sample_data()
        if count > 0:
            st.success(f"Loaded {count} sample notes across DBMS, OS, and ML.")
            st.rerun()
        else:
            st.info("Sample data already loaded.")

# Notes table
notes_df = get_notes()

if notes_df.empty:
    st.markdown(
        '<p style="color: var(--muted); margin-top: 48px;">'
        'No notes yet. Load sample data above or go to <strong>Summarize</strong> to upload your own.'
        '</p>',
        unsafe_allow_html=True,
    )
else:
    # Build the table with hairline dividers
    st.markdown(f'<p style="color: var(--muted); font-size: 0.88rem; margin-top: 24px;">'
                f'{len(notes_df)} notes in your library</p>', unsafe_allow_html=True)

    for _, row in notes_df.iterrows():
        cols = st.columns([4, 2, 1.5, 1.5])
        with cols[0]:
            st.markdown(f"**{row['title']}**")
        with cols[1]:
            st.markdown(f'<span style="color: var(--muted); font-size: 0.88rem;">{row["subject"]}</span>',
                        unsafe_allow_html=True)
        with cols[2]:
            created = str(row.get("created_at", ""))[:10]
            st.markdown(f'<span style="color: var(--muted); font-size: 0.88rem;">{created}</span>',
                        unsafe_allow_html=True)
        with cols[3]:
            if st.button("Open", key=f"open_{row['id']}"):
                st.session_state.current_note_id = int(row["id"])
                st.session_state.current_note_title = row["title"]
                st.switch_page("pages/1_Summarize.py")

        # Hairline divider
        st.markdown(
            '<hr style="margin: 4px 0; border: none; border-top: 1px solid var(--border);">',
            unsafe_allow_html=True,
        )
