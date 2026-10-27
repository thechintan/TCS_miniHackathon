"""
pages/4_Dashboard.py – Analytics dashboard with KPIs, charts, and recommendations.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from core.ui import NOTEWISE_CSS, sidebar, page_header
from modules.db import init_db, get_notes
from modules.dashboard import (
    get_kpis, notes_per_subject_chart, quiz_trend_chart,
    score_by_subject_chart, get_weak_topics, get_recommendations,
)
from modules.report import build_report, build_full_report

# ── Page setup ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dashboard – NoteWise", layout="wide", initial_sidebar_state="expanded")
st.markdown(NOTEWISE_CSS, unsafe_allow_html=True)
init_db()
sidebar()

# ── Header ────────────────────────────────────────────────────────────────
page_header("Dashboard", "Your study progress at a glance — what is working and what needs more attention.")

# ── KPIs ──────────────────────────────────────────────────────────────────
kpis = get_kpis()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total notes", kpis["total_notes"])
with col2:
    st.metric("Words processed", f'{kpis["total_words"]:,}')
with col3:
    st.metric("Avg compression", f'{kpis["avg_compression"]}%')
with col4:
    st.metric("Avg quiz score", f'{kpis["avg_quiz_score"]}%')

# ── Charts: two side by side ──────────────────────────────────────────────
st.markdown("")
col_left, col_right = st.columns(2)

with col_left:
    fig_subjects = notes_per_subject_chart()
    st.plotly_chart(fig_subjects, use_container_width=True, config={"displayModeBar": False})

with col_right:
    fig_scores = score_by_subject_chart()
    st.plotly_chart(fig_scores, use_container_width=True, config={"displayModeBar": False})

# ── Full-width weekly trend ───────────────────────────────────────────────
fig_trend = quiz_trend_chart()
st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

# ── Weak topics table ─────────────────────────────────────────────────────
weak = get_weak_topics()
if weak:
    st.markdown("### Topics that need attention")
    st.markdown(
        f'<p style="color: var(--muted); font-size: 0.88rem;">'
        f'{len(weak)} topic{"s" if len(weak) != 1 else ""} flagged as weak in your quizzes</p>',
        unsafe_allow_html=True,
    )

    # Table with hairline dividers
    header_html = (
        '<table style="width: 100%; border-collapse: collapse;">'
        '<thead><tr>'
        '<th style="text-align: left;">Subject</th>'
        '<th style="text-align: right;">Avg Score</th>'
        '<th style="text-align: left;">Recommendation</th>'
        '</tr></thead><tbody>'
    )
    rows_html = ""
    for w in weak:
        score_color = "#c0392b" if w["avg_score"] < 40 else "var(--text)"
        rows_html += (
            f'<tr>'
            f'<td style="text-align: left;">'
            f'<span class="weak-highlight">{w["subject"]}</span></td>'
            f'<td style="text-align: right;">'
            f'<span class="mono" style="color: {score_color};">{w["avg_score"]}%</span></td>'
            f'<td style="text-align: left; color: var(--muted); font-size: 0.9rem;">'
            f'{w["recommendation"]}</td>'
            f'</tr>'
        )
    table_html = header_html + rows_html + "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)

# ── Recommendations ───────────────────────────────────────────────────────
st.markdown("### Recommendations")
recs = get_recommendations()
for i, rec in enumerate(recs, 1):
    st.markdown(
        f'<div style="padding: 8px 0; border-bottom: 1px solid var(--border);">'
        f'<span class="mono" style="color: var(--muted); font-size: 0.82rem; margin-right: 8px;">{i}.</span>'
        f'{rec}</div>',
        unsafe_allow_html=True,
    )

# ── Report download ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Export")

col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    notes_df = get_notes()
    if not notes_df.empty:
        note_options = {f"{r['title']}": int(r['id']) for _, r in notes_df.iterrows()}
        selected = st.selectbox("Export single note", list(note_options.keys()))
        if selected:
            report = build_report(note_options[selected])
            st.download_button(
                "Download study sheet",
                data=report,
                file_name=f"{selected.lower().replace(' ', '_')}_study_sheet.md",
                mime="text/markdown",
            )

with col_dl2:
    st.markdown("")
    st.markdown("")
    full_report = build_full_report()
    st.download_button(
        "Download full report",
        data=full_report,
        file_name="notewise_full_report.md",
        mime="text/markdown",
    )
