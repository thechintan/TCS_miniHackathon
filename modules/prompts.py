"""
modules/prompts.py – All LLM prompt templates.
"""

SUMMARY_SYSTEM = (
    "You are a study assistant for university students. "
    "You produce clear, accurate, and concise summaries. "
    "Never add information that is not in the source notes."
)

SUMMARY_SHORT = """Summarize the following notes in 5 to 7 lines for a university student.
Use simple language. Focus on the most important concepts.

NOTES:
{text}"""

SUMMARY_DETAILED = """Provide a detailed summary of the following notes for a university student.
Cover all major topics, definitions, and examples. Use clear paragraphs.
Length: 15 to 20 lines.

NOTES:
{text}"""

SUMMARY_EXAM = """Create an exam-focused summary of the following notes.
For each major topic, list: (1) the definition, (2) why it matters, (3) a likely exam question.
Be concise but thorough.

NOTES:
{text}"""

KEY_POINTS = """Extract 5 to 8 key points from the following notes as a JSON array of strings.
Each point should be one clear sentence. Return ONLY the JSON array, nothing else.

NOTES:
{text}"""

FLASHCARDS = """Generate {n} flashcards from the following notes.
Return a JSON array of objects, each with "q" (question) and "a" (answer).
Questions should test understanding, not just recall.
Return ONLY the JSON array, nothing else.

NOTES:
{text}"""

QUIZ = """Generate {n} multiple-choice quiz questions from the following notes.
Return a JSON array of objects, each with:
- "question": the question text
- "options": array of 4 answer choices
- "answer_index": index (0-3) of the correct answer
- "explanation": brief explanation of why the answer is correct
Return ONLY the JSON array, nothing else.

NOTES:
{text}"""

RAG_ANSWER = """Answer the student's question using ONLY the context below.
If the answer is not in the context, say "I don't have enough information in your notes to answer that."
Be specific and cite which part of the notes supports your answer.

CONTEXT:
{context}

QUESTION:
{question}"""

MAP_REDUCE_COMBINE = """Below are summaries of different sections of the same document.
Combine them into one coherent summary of 5 to 7 lines. Remove redundancy.

SECTION SUMMARIES:
{summaries}"""
