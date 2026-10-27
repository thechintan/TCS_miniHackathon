"""
modules/dashboard.py – Dashboard analytics: KPIs, charts, weak topics, recommendations.
"""
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional

from modules.db import get_notes, get_quiz_scores, get_all_summaries


# ── Design tokens ─────────────────────────────────────────────────────────
_ACCENT = "#1F3A5F"
_BG = "#FFFFFF"
_GRID = "#E6E2DA"
_TEXT = "#1A1A1A"
_MUTED = "#6B6B6B"

_CHART_LAYOUT = dict(
    plot_bgcolor=_BG,
    paper_bgcolor=_BG,
    font=dict(family="Instrument Sans, system-ui, sans-serif", color=_TEXT, size=13),
    margin=dict(l=48, r=24, t=36, b=48),
    xaxis=dict(showgrid=True, gridcolor=_GRID, gridwidth=1, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor=_GRID, gridwidth=1, zeroline=False),
)


def get_kpis() -> dict:
    """Return dashboard KPI values."""
    notes = get_notes()
    summaries = get_all_summaries()
    scores = get_quiz_scores()

    total_notes = len(notes)
    total_words = int(notes["word_count"].sum()) if not notes.empty else 0

    # Average compression ratio
    if not summaries.empty and "note_words" in summaries.columns and "summary_words" in summaries.columns:
        valid = summaries[(summaries["note_words"] > 0) & (summaries["summary_words"] > 0)]
        if not valid.empty:
            avg_compression = round(
                (1 - valid["summary_words"].sum() / valid["note_words"].sum()) * 100
            )
        else:
            avg_compression = 0
    else:
        avg_compression = 0

    # Average quiz score
    if not scores.empty:
        scores["pct"] = scores["score"] / scores["total"] * 100
        avg_quiz = round(scores["pct"].mean())
    else:
        avg_quiz = 0

    return {
        "total_notes": total_notes,
        "total_words": total_words,
        "avg_compression": avg_compression,
        "avg_quiz_score": avg_quiz,
        "summaries_count": len(summaries),
        "quizzes_taken": len(scores),
    }


def notes_per_subject_chart() -> go.Figure:
    """Bar chart: notes per subject."""
    notes = get_notes()
    if notes.empty:
        return _empty_chart("No notes yet")

    counts = notes.groupby("subject").size().reset_index(name="count")
    counts = counts.sort_values("count", ascending=True)

    fig = go.Figure(go.Bar(
        x=counts["count"],
        y=counts["subject"],
        orientation="h",
        marker_color=_ACCENT,
        text=counts["count"],
        textposition="outside",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        title=dict(text="Notes per subject", font=dict(size=14)),
        xaxis_title="Count",
        yaxis_title="",
        height=max(200, len(counts) * 40 + 100),
    )
    return fig


def quiz_trend_chart() -> go.Figure:
    """Line chart: quiz score over time."""
    scores = get_quiz_scores()
    if scores.empty:
        return _empty_chart("No quiz scores yet")

    scores["pct"] = (scores["score"] / scores["total"] * 100).round()
    scores["taken_at"] = pd.to_datetime(scores["taken_at"])
    scores = scores.sort_values("taken_at")

    fig = go.Figure(go.Scatter(
        x=scores["taken_at"],
        y=scores["pct"],
        mode="lines+markers",
        line=dict(color=_ACCENT, width=2),
        marker=dict(color=_ACCENT, size=6),
        hovertemplate="Score: %{y}%<br>Date: %{x|%b %d}<extra></extra>",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        title=dict(text="Quiz scores over time", font=dict(size=14)),
        xaxis_title="Date",
        yaxis_title="Score (%)",
        yaxis_range=[0, 105],
        height=300,
    )
    return fig


def score_by_subject_chart() -> go.Figure:
    """Bar chart: average quiz score per subject."""
    scores = get_quiz_scores()
    if scores.empty:
        return _empty_chart("No quiz scores yet")

    scores["pct"] = (scores["score"] / scores["total"] * 100).round()
    subject_col = "subject" if "subject" in scores.columns and scores["subject"].notna().any() else "note_subject"

    if subject_col not in scores.columns or scores[subject_col].isna().all():
        return _empty_chart("No subject data available")

    avg = scores.groupby(subject_col)["pct"].mean().round().reset_index()
    avg.columns = ["subject", "avg_score"]
    avg = avg.sort_values("avg_score", ascending=True)

    fig = go.Figure(go.Bar(
        x=avg["avg_score"],
        y=avg["subject"],
        orientation="h",
        marker_color=_ACCENT,
        text=[f"{v:.0f}%" for v in avg["avg_score"]],
        textposition="outside",
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        title=dict(text="Average score by subject", font=dict(size=14)),
        xaxis_title="Average Score (%)",
        xaxis_range=[0, 105],
        yaxis_title="",
        height=max(200, len(avg) * 40 + 100),
    )
    return fig


def get_weak_topics() -> list[dict]:
    """Subjects/topics with average quiz score below 60%."""
    scores = get_quiz_scores()
    if scores.empty:
        return []

    scores["pct"] = (scores["score"] / scores["total"] * 100).round()
    subject_col = "subject" if "subject" in scores.columns and scores["subject"].notna().any() else "note_subject"

    if subject_col not in scores.columns:
        return []

    avg = scores.groupby(subject_col)["pct"].mean().round().reset_index()
    avg.columns = ["subject", "avg_score"]
    weak = avg[avg["avg_score"] < 60].sort_values("avg_score")

    return [
        {"subject": row["subject"], "avg_score": int(row["avg_score"]),
         "recommendation": f"Review {row['subject']} notes and retake the quiz — your average is {int(row['avg_score'])}%"}
        for _, row in weak.iterrows()
    ]


def get_recommendations() -> list[str]:
    """Generate prioritized study recommendations."""
    weak = get_weak_topics()
    kpis = get_kpis()
    recs = []

    for w in weak:
        recs.append(w["recommendation"])

    if kpis["total_notes"] > 0 and kpis["summaries_count"] == 0:
        recs.append(f"You have {kpis['total_notes']} notes but no summaries yet — start summarizing to improve retention")

    if kpis["quizzes_taken"] == 0 and kpis["total_notes"] > 0:
        recs.append("Take your first quiz to start tracking progress")

    if kpis["avg_quiz_score"] > 0 and kpis["avg_quiz_score"] < 70:
        recs.append(f"Your overall average is {kpis['avg_quiz_score']}% — aim for 80% or higher through targeted review")

    if not recs:
        recs.append("Keep up the good work — all subjects are above 60%")

    return recs


def _empty_chart(message: str) -> go.Figure:
    """Return an empty chart with a message."""
    fig = go.Figure()
    fig.update_layout(
        **_CHART_LAYOUT,
        height=200,
        annotations=[dict(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color=_MUTED),
        )],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
