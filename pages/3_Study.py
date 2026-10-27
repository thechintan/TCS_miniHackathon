"""
pages/3_Study.py – Flashcards and Quiz study tools.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from core.ui import NOTEWISE_CSS, sidebar, page_header
from modules.db import init_db, get_notes, get_note, get_summary, save_quiz_score
from modules.summarizer import mock_summarize_result

# ── Page setup ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Study – NoteWise", layout="wide", initial_sidebar_state="expanded")
st.markdown(NOTEWISE_CSS, unsafe_allow_html=True)
init_db()
sidebar()

# ── Session defaults ──────────────────────────────────────────────────────
if "current_note_id" not in st.session_state:
    st.session_state.current_note_id = None
if "current_note_title" not in st.session_state:
    st.session_state.current_note_title = "No note open"
if "fc_index" not in st.session_state:
    st.session_state.fc_index = 0
if "fc_show_answer" not in st.session_state:
    st.session_state.fc_show_answer = False
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

# ── Header ────────────────────────────────────────────────────────────────
page_header("Study", "Test yourself with flashcards and quizzes generated from your notes.")

# ── Note selector ─────────────────────────────────────────────────────────
notes_df = get_notes()
if notes_df.empty:
    st.markdown(
        '<p style="color: var(--muted); margin-top: 24px;">'
        'No notes yet. Go to <strong>Summarize</strong> to upload and process notes first.</p>',
        unsafe_allow_html=True,
    )
    st.stop()

note_options = {f"{r['title']} ({r['subject']})": int(r['id']) for _, r in notes_df.iterrows()}
selected_label = st.selectbox("Select a note to study", list(note_options.keys()))
note_id = note_options[selected_label]
note_data = get_note(note_id)
summary_data = get_summary(note_id)

# Load study data or generate dynamically from note content
if summary_data and (summary_data.get("flashcards") or summary_data.get("quiz")):
    flashcards = summary_data.get("flashcards", [])
    quiz_questions = summary_data.get("quiz", [])
else:
    content = note_data.get("content", "") if note_data else ""
    mock = mock_summarize_result(content)
    flashcards = mock["flashcards"]
    quiz_questions = mock["quiz"]

# ── Tabs ──────────────────────────────────────────────────────────────────
tab_fc, tab_quiz = st.tabs(["Flashcards", "Quiz"])

# ── Flashcards tab ────────────────────────────────────────────────────────
with tab_fc:
    if not flashcards:
        st.markdown('<p style="color: var(--muted);">No flashcards available. Summarize this note first.</p>',
                    unsafe_allow_html=True)
    else:
        total = len(flashcards)
        idx = st.session_state.fc_index % total
        fc = flashcards[idx]
        q = fc.get("q", fc.get("question", ""))
        a = fc.get("a", fc.get("answer", ""))

        st.markdown(
            f'<div class="flashcard-counter">Card {idx + 1} of {total}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="flashcard">'
            f'<div class="flashcard-question">{q}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col_reveal, col_prev, col_next = st.columns([2, 1, 1])

        with col_reveal:
            if st.button("Reveal answer"):
                st.session_state.fc_show_answer = True

        with col_prev:
            if st.button("Previous"):
                st.session_state.fc_index = (idx - 1) % total
                st.session_state.fc_show_answer = False
                st.rerun()

        with col_next:
            if st.button("Next"):
                st.session_state.fc_index = (idx + 1) % total
                st.session_state.fc_show_answer = False
                st.rerun()

        if st.session_state.fc_show_answer:
            st.markdown(
                f'<div class="flashcard">'
                f'<div class="flashcard-answer">{a}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── Quiz tab ──────────────────────────────────────────────────────────────
with tab_quiz:
    if not quiz_questions:
        st.markdown('<p style="color: var(--muted);">No quiz available. Summarize this note first.</p>',
                    unsafe_allow_html=True)
    else:
        if not st.session_state.quiz_submitted:
            with st.form("quiz_form"):
                st.markdown(f'<p style="color: var(--muted); font-size: 0.88rem;">'
                            f'{len(quiz_questions)} questions</p>', unsafe_allow_html=True)

                user_answers = {}
                for i, q in enumerate(quiz_questions):
                    st.markdown(f"**{i + 1}. {q['question']}**")
                    options = q.get("options", [])
                    answer = st.radio(
                        f"Question {i + 1}",
                        options,
                        key=f"quiz_q_{i}",
                        label_visibility="collapsed",
                    )
                    user_answers[i] = options.index(answer) if answer in options else -1
                    st.markdown("")

                submitted = st.form_submit_button("Submit quiz")

                if submitted:
                    st.session_state.quiz_answers = user_answers
                    st.session_state.quiz_submitted = True
                    st.rerun()
        else:
            # Show results
            user_answers = st.session_state.quiz_answers
            correct = 0
            total_q = len(quiz_questions)

            for i, q in enumerate(quiz_questions):
                user_ans = user_answers.get(i, -1)
                correct_idx = q.get("answer_index", 0)
                is_correct = user_ans == correct_idx
                if is_correct:
                    correct += 1

                options = q.get("options", [])
                st.markdown(f"**{i + 1}. {q['question']}**")

                if is_correct:
                    st.markdown(f'<span style="color: #2d7d46;">Correct: {options[correct_idx]}</span>',
                                unsafe_allow_html=True)
                else:
                    user_choice = options[user_ans] if 0 <= user_ans < len(options) else "No answer"
                    st.markdown(
                        f'<span style="color: #c0392b;">Your answer: {user_choice}</span><br>'
                        f'<span style="color: #2d7d46;">Correct: {options[correct_idx]}</span>',
                        unsafe_allow_html=True,
                    )

                explanation = q.get("explanation", "")
                if explanation:
                    st.markdown(f'<span style="color: var(--muted); font-size: 0.88rem;">{explanation}</span>',
                                unsafe_allow_html=True)
                st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid var(--border);">',
                            unsafe_allow_html=True)

            # Score display
            st.markdown(
                f'<div style="margin-top: 24px;">'
                f'<span class="mono-large">{correct} of {total_q}</span>'
                f'<span style="color: var(--muted); margin-left: 8px;">correct</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Save score
            subject = note_data["subject"] if note_data else ""
            save_quiz_score(note_id, correct, total_q, subject=subject)

            st.markdown("")
            if st.button("Retake quiz"):
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {}
                st.rerun()
