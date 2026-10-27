"""
modules/report.py – Export study reports as Markdown or PDF.
"""
import json
from datetime import datetime
from typing import Optional

from modules.db import get_note, get_summary, get_notes, get_quiz_scores, get_all_summaries


def build_report(note_id: int) -> str:
    """Build a Markdown study sheet for a single note."""
    note = get_note(note_id)
    if not note:
        return "# Note not found"

    summary_data = get_summary(note_id)
    lines = [
        f"# Study Report: {note['title']}",
        f"**Subject:** {note['subject']}  ",
        f"**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}  ",
        f"**Original length:** {note['word_count']} words  ",
        "",
    ]

    if summary_data:
        lines.append("---")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(summary_data["summary"])
        lines.append("")

        if summary_data.get("key_points"):
            lines.append("## Key Points")
            lines.append("")
            for kp in summary_data["key_points"]:
                lines.append(f"- {kp}")
            lines.append("")

        if summary_data.get("flashcards"):
            lines.append("## Flashcards")
            lines.append("")
            for i, fc in enumerate(summary_data["flashcards"], 1):
                q = fc.get("q", fc.get("question", ""))
                a = fc.get("a", fc.get("answer", ""))
                lines.append(f"**Q{i}.** {q}  ")
                lines.append(f"**A:** {a}")
                lines.append("")

        sw = summary_data.get("summary_words", 0)
        if sw and note["word_count"]:
            ratio = round((1 - sw / note["word_count"]) * 100)
            lines.append(f"---")
            lines.append(f"*Compressed {note['word_count']} words to {sw} ({ratio}% reduction)*")
    else:
        lines.append("*No summary generated yet. Summarize this note first.*")

    return "\n".join(lines)


def build_full_report() -> str:
    """Build a Markdown study sheet for all notes."""
    notes = get_notes()
    if notes.empty:
        return "# No Notes\n\nUpload some notes to generate a full report."

    lines = [
        "# Complete Study Report",
        f"**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}  ",
        f"**Total notes:** {len(notes)}  ",
        "",
        "---",
        "",
    ]

    for _, note_row in notes.iterrows():
        note_id = note_row["id"]
        note = get_note(note_id)
        if not note:
            continue

        lines.append(f"## {note['title']}")
        lines.append(f"*{note['subject']} · {note['word_count']} words*")
        lines.append("")

        summary_data = get_summary(note_id)
        if summary_data:
            lines.append(summary_data["summary"])
            lines.append("")

            if summary_data.get("key_points"):
                lines.append("### Key Points")
                for kp in summary_data["key_points"]:
                    lines.append(f"- {kp}")
                lines.append("")
        else:
            lines.append("*Not yet summarized.*")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Quiz performance summary
    scores = get_quiz_scores()
    if not scores.empty:
        lines.append("## Quiz Performance")
        lines.append("")
        scores["pct"] = (scores["score"] / scores["total"] * 100).round()
        avg = scores["pct"].mean()
        lines.append(f"**Average score:** {avg:.0f}%  ")
        lines.append(f"**Quizzes taken:** {len(scores)}  ")
        lines.append("")

    return "\n".join(lines)


def build_pdf_report(note_id: int) -> Optional[bytes]:
    """Build a PDF report for a single note. Returns bytes or None."""
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    note = get_note(note_id)
    if not note:
        return None

    summary_data = get_summary(note_id)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Study Report: {note['title']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Subject: {note['subject']}  |  {note['word_count']} words", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    if summary_data:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, summary_data["summary"])
        pdf.ln(5)

        if summary_data.get("key_points"):
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 10, "Key Points", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            for kp in summary_data["key_points"]:
                pdf.multi_cell(0, 6, f"  - {kp}")
            pdf.ln(5)

        if summary_data.get("flashcards"):
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 10, "Flashcards", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            for i, fc in enumerate(summary_data["flashcards"], 1):
                q = fc.get("q", fc.get("question", ""))
                a = fc.get("a", fc.get("answer", ""))
                pdf.set_font("Helvetica", "B", 11)
                pdf.multi_cell(0, 6, f"Q{i}. {q}")
                pdf.set_font("Helvetica", "", 11)
                pdf.multi_cell(0, 6, f"A: {a}")
                pdf.ln(3)

    return pdf.output()
